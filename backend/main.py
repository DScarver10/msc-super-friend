from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import load_settings
from backend.logging_setup import setup_logging
from backend.rag.ingest import ingest

setup_logging()
logger = logging.getLogger("backend")

settings = load_settings()
app = FastAPI(title="MSC Super Friend Backend", version=settings.app_version)

# CORS for hosted Streamlit frontend (set tight later; permissive for MVP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

INDEX_STATE = {"indexed_as_of": "not indexed", "num_chunks": 0, "sources": []}

# ----------------------------
# Feedback storage
# ----------------------------
# Use an absolute path rooted at the repo so it behaves predictably on Render.
REPO_ROOT = Path(__file__).resolve().parents[1]
FEEDBACK_PATH = REPO_ROOT / "backend" / "data" / "feedback.jsonl"
FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)


class FeedbackEvent(BaseModel):
    vote: str  # "up" | "down" | "down_note"
    question_id: str
    answer_id: str
    question: str
    answer: str
    citations: list = []
    notes: str | None = None
    ts: int | None = None


@app.get("/")
def root():
    """
    Simple root route so the base Render URL doesn't return 404.
    Helps sanity-check that the service is up without needing /docs.
    """
    return {
        "ok": True,
        "service": "msc-super-friend-backend",
        "version": settings.app_version,
        "message": "Backend is running. Visit /docs for API documentation.",
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "msc-super-friend-backend",
        "model": settings.llm_model,
        "version": settings.app_version,
        "indexed_as_of": INDEX_STATE["indexed_as_of"],
        "num_chunks": INDEX_STATE["num_chunks"],
        "sources": INDEX_STATE["sources"],
    }


@app.get("/version")
def version():
    return {
        "backend_version": settings.app_version,
        "indexed_as_of": INDEX_STATE["indexed_as_of"],
        "num_chunks": INDEX_STATE["num_chunks"],
    }


@app.post("/ingest")
def ingest_endpoint():
    """
    Builds/refreshes the vector index from sources.yaml + local toolkit docs.
    """
    try:
        result = ingest(
            settings.sources_path,
            settings.index_dir,
            settings.toolkit_docs_dir,
        )
        INDEX_STATE["indexed_as_of"] = result.indexed_as_of
        INDEX_STATE["num_chunks"] = result.num_chunks
        INDEX_STATE["sources"] = result.sources
        return {
            **INDEX_STATE,
            "skipped_items": result.skipped_items,
        }
    except Exception as e:
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
def record_feedback(event: FeedbackEvent):
    """
    Records thumbs up/down feedback from the frontend.
    Stored as append-only JSONL for later analysis.
    """
    payload = event.model_dump()
    payload["ts"] = payload["ts"] or int(time.time())

    try:
        with FEEDBACK_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

        logger.info(
            "Feedback recorded",
            extra={
                "vote": payload.get("vote"),
                "question_id": payload.get("question_id"),
                "answer_id": payload.get("answer_id"),
            },
        )
        return {"ok": True}

    except Exception:
        logger.exception("Failed to record feedback")
        raise HTTPException(status_code=500, detail="Failed to record feedback")
