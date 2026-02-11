from __future__ import annotations

import logging
import os
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
from dotenv import load_dotenv
import os

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# quick sanity check (remove after confirming)
print("OPENAI_API_KEY present?", bool(os.getenv("OPENAI_API_KEY")))

app = FastAPI(title="MSC Super Companion API", version="0.1.0")
logger = logging.getLogger("api")


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


def _index_dir() -> Path:
    root = Path(__file__).resolve().parents[1]
    default = root / "backend" / "data" / "index"
    return Path(os.getenv("INDEX_DIR", str(default))).resolve()


def _docs_url(local_path: str | None) -> str | None:
    if not local_path:
        return None
    name = Path(local_path).name
    if not name:
        return None
    return f"/docs/{quote(name)}"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask")
def ask(payload: AskRequest) -> dict[str, object]:
    idx_dir = _index_dir()
    index_file = idx_dir / "faiss.index"
    meta_file = idx_dir / "meta.json"

    if not index_file.exists() or not meta_file.exists():
        raise HTTPException(
            status_code=503,
            detail=(
                "RAG index is unavailable. Build it first (expected files: "
                f"{index_file} and {meta_file})."
            ),
        )

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Missing OPENAI_API_KEY. Set it in the environment before calling /ask.",
        )

    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip()

    try:
        from backend.rag.llm import generate_grounded_answer
        from backend.rag.retrieve import retrieve
    except Exception as exc:
        logger.exception("RAG dependency import failed")
        raise HTTPException(
            status_code=500,
            detail=(
                "RAG dependencies are missing or misconfigured. "
                "Install API/backend requirements (e.g., faiss-cpu, openai, numpy)."
            ),
        ) from exc

    try:
        evidence = retrieve(
            index_dir=idx_dir,
            question=payload.question,
            top_k=5,
            api_key=api_key,
            embedding_model=embedding_model,
        )

        answer = generate_grounded_answer(
            api_key=api_key,
            model=llm_model,
            question=payload.question,
            evidence=evidence,
        )

        citations = [
            {
                "title": item.title,
                "url": item.url or _docs_url(item.local_path) or "",
                "snippet": item.excerpt,
            }
            for item in evidence
        ]

        return {
            "answer": answer,
            "citations": citations,
        }

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="RAG index files are missing. Run ingestion to rebuild the index.",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("RAG ask failed")
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to generate an answer. Check dependencies and runtime config "
                "(OPENAI_API_KEY, model availability, FAISS index)."
            ),
        ) from exc
