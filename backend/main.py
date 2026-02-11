from __future__ import annotations

import json
import logging
import os
import re
import time
from uuid import uuid4
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import FileResponse

from backend.config import load_settings
from backend.logging_setup import setup_logging
from backend.rag.ingest import ingest
from backend.rag.llm import generate_grounded_answer  # your existing function

try:
    from backend.rag.retrieve import retrieve_with_trace
except ImportError:
    # Backward compatibility for environments that still expose only `retrieve`.
    from backend.rag.retrieve import retrieve as _retrieve_only

    class _FallbackTrace:
        def __init__(self, question: str, top_k: int) -> None:
            self._question = question
            self._top_k = top_k

        def to_dict(self) -> dict:
            return {
                "query": self._question,
                "normalized_query": self._question,
                "routed_domain": "unknown",
                "top_k": self._top_k,
                "candidate_count": 0,
                "vector_weight": None,
                "lexical_weight": None,
                "rerank_mode": "compat_fallback",
                "selected": [],
            }

    def retrieve_with_trace(
        index_dir: Path,
        question: str,
        top_k: int = 5,
        allowed_sources: Optional[List[str]] = None,
        api_key: str | None = None,
        embedding_model: str = "text-embedding-3-small",
        vector_weight: float = 0.75,
        lexical_weight: float = 0.25,
        rerank_mode: str = "heuristic",
    ):
        evidence = _retrieve_only(
            index_dir=index_dir,
            question=question,
            top_k=top_k,
            allowed_sources=allowed_sources,
            api_key=api_key,
            embedding_model=embedding_model,
        )
        return evidence, _FallbackTrace(question=question, top_k=top_k)

setup_logging()
logger = logging.getLogger("backend")

settings = load_settings()
app = FastAPI(title="MSC Super Companion Backend", version=getattr(settings, "app_version", "0.1.0"))

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
RETRIEVAL_TRACE_PATH = Path("backend/data/retrieval_traces.jsonl")
RETRIEVAL_TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)

DOCS_DIR = Path(getattr(settings, "docs_dir", "")) if getattr(settings, "docs_dir", "") else Path(__file__).resolve().parents[1] / "backend" / "data" / "toolkit_docs"
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

        # Case-insensitive fallback for Linux hosts when source names vary in case.
        target = rel.name.casefold()
        if root.exists():
            for child in root.iterdir():
                if child.is_file() and child.name.casefold() == target:
                    return child.resolve()
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
    section: Optional[str] = None
    subsection: Optional[str] = None
    pub: Optional[str] = None
    domain: Optional[str] = None
    doc_type: Optional[str] = None
    score: float


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: List[Citation]
    question_id: str
    answer_id: str
    grounded: bool = False
    indexed_as_of: str = "unknown"
    retrieval_trace_id: str | None = None


def _answer_has_citation_markers(answer: str) -> bool:
    return bool(re.search(r"\[E\d+\]", answer or ""))


def _is_grounded(evidence: list[Citation], answer: str, min_top_score: float) -> bool:
    if not evidence:
        return False
    if max((c.score for c in evidence), default=0.0) < min_top_score:
        return False
    return _answer_has_citation_markers(answer)


def _citation_has_locator(citation: Citation) -> bool:
    if citation.page is not None:
        return True
    if citation.section and citation.section.strip():
        return True
    if citation.subsection and citation.subsection.strip():
        return True
    return False


def _write_retrieval_trace(payload: dict) -> str:
    trace_id = payload.get("trace_id") or str(uuid4())
    payload["trace_id"] = trace_id
    with RETRIEVAL_TRACE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return trace_id


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

        vector_weight = float(os.getenv("RAG_VECTOR_WEIGHT", "0.75"))
        lexical_weight = float(os.getenv("RAG_LEXICAL_WEIGHT", "0.25"))
        rerank_mode = os.getenv("RAG_RERANK_MODE", "heuristic").strip().lower() or "heuristic"
        min_top_score = float(os.getenv("RAG_MIN_TOP_SCORE", "0.2"))

        evidence, retrieval_trace = retrieve_with_trace(
            index_dir=index_dir,
            question=req.question,
            top_k=req.top_k,
            allowed_sources=req.allowed_sources,
            api_key=api_key,
            embedding_model=getattr(settings, "embedding_model", "text-embedding-3-small"),
            vector_weight=vector_weight,
            lexical_weight=lexical_weight,
            rerank_mode=rerank_mode,
        )

        # Build an evidence pack for the LLM (IDs E1..)
        # Your generate_grounded_answer already expects a list of Evidence with evid_id + excerpt.
        if evidence:
            answer_text = generate_grounded_answer(
                api_key=api_key,
                model=getattr(settings, "llm_model", "gpt-4o-mini"),
                question=req.question,
                evidence=evidence,
            )
        else:
            answer_text = "Insufficient evidence in the indexed sources."

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
                section=e.section,
                subsection=e.subsection,
                pub=e.pub,
                domain=e.domain,
                doc_type=e.doc_type,
                score=e.score,
            )
            for e in evidence
        ]

        # Prefer fewer precise citations over many weak ones.
        precise_citations = [c for c in citations if _citation_has_locator(c)]
        precise_citations.sort(key=lambda c: c.score, reverse=True)
        citations = precise_citations[:3]

        grounded = _is_grounded(citations, answer_text, min_top_score=min_top_score)
        if not grounded:
            answer_text = "Insufficient evidence in the indexed sources."

        trace_id: str | None = None
        try:
            trace_payload = {
                "ts": int(time.time()),
                "question": req.question,
                "top_k": req.top_k,
                "allowed_sources": req.allowed_sources or [],
                "retrieval": retrieval_trace.to_dict(),
                "grounded": grounded,
                "citation_count": len(citations),
                "top_score": max((c.score for c in citations), default=0.0),
            }
            trace_id = _write_retrieval_trace(trace_payload)
            logger.info(
                "retrieval_trace_id=%s grounded=%s citations=%s",
                trace_id,
                grounded,
                len(citations),
            )
        except Exception:
            logger.exception("Failed to persist retrieval trace")

        return AskResponse(
            question=req.question,
            answer=answer_text,
            citations=citations,
            question_id=qid,
            answer_id=aid,
            grounded=grounded,
            indexed_as_of=INDEX_STATE["indexed_as_of"],
            retrieval_trace_id=trace_id,
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
