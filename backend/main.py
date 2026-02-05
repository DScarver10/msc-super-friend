from __future__ import annotations

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
    try:
        result = ingest(settings.sources_path, settings.index_dir, settings.toolkit_docs_dir)
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


