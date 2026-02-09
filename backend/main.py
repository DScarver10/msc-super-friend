from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import FileResponse

from backend.config import load_settings
from backend.logging_setup import setup_logging
from backend.rag.ingest import ingest
from backend.rag.retrieve import retrieve
from backend.rag.llm import generate_grounded_answer  # your existing function

setup_logging()
logger = logging.getLogger("backend")

settings = load_settings()
app = FastAPI(title="MSC Super Friend Backend", version=getattr(settings, "app_version", "0.1.0"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten later
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

INDEX_STATE = {"indexed_as_of": "not indexed", "num_chunks": 0, "sources": []}

FEEDBACK_PATH = Path("backend/data/feedback.jsonl")
FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)

DOCS_DIR = Path(getattr(settings, "docs_dir", "")) if getattr(settings, "docs_dir", "") else Path(__file__).resolve().parents[1] / "frontend" / "docs"
DOCS_DIR = DOCS_DIR.resolve()


def _doc_roots() -> list[Path]:
    repo_root = Path(__file__).resolve().parents[1]
    roots = [
        DOCS_DIR,
        (repo_root / "backend" / "data" / "toolkit_docs").resolve(),
        (repo_root / "frontend" / "docs").resolve(),
    ]
    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root)
        if key not in seen:
            seen.add(key)
            unique.append(root)
    return unique


def _resolve_doc_path(file_path: str) -> Path | None:
    rel = Path(file_path)
    if ".." in rel.parts:
        raise HTTPException(status_code=400, detail="Invalid path")

    for root in _doc_roots():
        candidate = (root / rel).resolve()
        if str(candidate).startswith(str(root)) and candidate.exists() and candidate.is_file():
            return candidate

        # Fallback: allow /docs/<filename> style lookups by basename.
        by_name = (root / rel.name).resolve()
        if str(by_name).startswith(str(root)) and by_name.exists() and by_name.is_file():
            return by_name
    return None


class FeedbackEvent(BaseModel):
    vote: str                  # "up" | "down" | "down_note"
    question_id: str
    answer_id: str
    question: str
    answer: str
    citations: list = []
    notes: str | None = None
    ts: int | None = None


class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    allowed_sources: Optional[List[str]] = None


class Citation(BaseModel):
    evid_id: str
    title: str
    excerpt: str
    url: Optional[str] = None
    local_path: Optional[str] = None
    page: Optional[int] = None
    score: float


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: List[Citation]
    question_id: str
    answer_id: str


@app.get("/")
def root():
    # helpful for Render: visiting service URL should not be "Not Found"
    return {"ok": True, "service": "msc-super-friend-backend"}


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "msc-super-friend-backend",
        "model": getattr(settings, "llm_model", "unknown"),
        "version": getattr(settings, "app_version", "0.1.0"),
        "indexed_as_of": INDEX_STATE["indexed_as_of"],
        "num_chunks": INDEX_STATE["num_chunks"],
        "sources": INDEX_STATE["sources"],
    }


@app.get("/docs/{file_path:path}")
def serve_docs(file_path: str):
    resolved = _resolve_doc_path(file_path)
    if not resolved:
        raise HTTPException(status_code=404, detail="File not found")

    media_type = "application/pdf"
    if resolved.suffix.lower() == ".xlsx":
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    headers = {"Content-Disposition": f'inline; filename="{resolved.name}"'}
    return FileResponse(
        path=str(resolved),
        media_type=media_type,
        headers=headers,
    )


@app.post("/ingest")
def ingest_endpoint():
    try:
        sources_path = Path(settings.sources_path)
        index_dir = Path(settings.index_dir)
        toolkit_docs_dir = Path(settings.toolkit_docs_dir) if getattr(settings, "toolkit_docs_dir", None) else None

        result = ingest(
            sources_path=sources_path,
            index_dir=index_dir,
            toolkit_docs_dir=toolkit_docs_dir,
            api_key=getattr(settings, "openai_api_key", None) or None,
            embedding_model=getattr(settings, "embedding_model", "text-embedding-3-small"),
        )

        INDEX_STATE["indexed_as_of"] = result.indexed_as_of
        INDEX_STATE["num_chunks"] = result.num_chunks
        INDEX_STATE["sources"] = result.sources

        return {**INDEX_STATE, "skipped_items": result.skipped_items}

    except Exception as e:
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """
    UI-friendly ask endpoint:
    - input: { question, top_k, allowed_sources }
    - output: { answer, citations[] } with clickable urls
    """
    try:
        index_dir = Path(settings.index_dir)

        if not (index_dir / "faiss.index").exists() or not (index_dir / "meta.json").exists():
            raise HTTPException(status_code=400, detail="Index not built yet. Run /ingest first.")

        api_key = getattr(settings, "openai_api_key", None)
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY on backend.")

        evidence = retrieve(
            index_dir=index_dir,
            question=req.question,
            top_k=req.top_k,
            allowed_sources=req.allowed_sources,
            api_key=api_key,
            embedding_model=getattr(settings, "embedding_model", "text-embedding-3-small"),
        )

        # Build an evidence pack for the LLM (IDs E1..)
        # Your generate_grounded_answer already expects a list of Evidence with evid_id + excerpt.
        answer_text = generate_grounded_answer(
            api_key=api_key,
            model=getattr(settings, "llm_model", "gpt-4o-mini"),
            question=req.question,
            evidence=evidence,
        )

        ts = int(time.time())
        qid = f"q_{ts}"
        aid = f"a_{ts}"

        citations = [
            Citation(
                evid_id=e.evid_id,
                title=e.title,
                excerpt=e.excerpt,
                url=e.url,
                local_path=e.local_path,
                page=e.page,
                score=e.score,
            )
            for e in evidence
        ]

        return AskResponse(
            question=req.question,
            answer=answer_text,
            citations=citations,
            question_id=qid,
            answer_id=aid,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Ask failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
def record_feedback(event: FeedbackEvent):
    payload = event.dict()
    payload["ts"] = payload["ts"] or int(time.time())

    try:
        with FEEDBACK_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return {"ok": True}
    except Exception:
        logger.exception("Failed to record feedback")
        raise HTTPException(status_code=500, detail="Failed to record feedback")
