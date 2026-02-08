from __future__ import annotations

import logging
import os
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.responses import FileResponse
from pydantic import BaseModel, Field

API_DIR = Path(__file__).resolve().parent
load_dotenv(Path(__file__).resolve().parent / ".env", override=True, encoding="utf-8-sig")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="MSC Super Friend API", version="0.1.0")
logger = logging.getLogger("api")


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error. Check server logs."})


@app.on_event("startup")
def log_resolved_paths() -> None:
    resolved_index_dir = index_dir()
    meta_path = resolved_index_dir / "meta.json"
    faiss_path = resolved_index_dir / "faiss.index"
    logger.info("Using INDEX_DIR=%s", resolved_index_dir)
    logger.info("meta.json exists: %s (%s)", meta_path.exists(), meta_path)
    logger.info("faiss.index exists: %s (%s)", faiss_path.exists(), faiss_path)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None:
        # Handle UTF-8 BOM-prefixed first key in .env files.
        value = os.getenv(f"\ufeff{name}", default)
    return str(value).strip()


def index_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    default_index_dir = repo_root / "backend" / "data" / "index"
    raw_index_dir = _env("INDEX_DIR")
    if not raw_index_dir:
        return default_index_dir.resolve()

    configured = Path(raw_index_dir).expanduser()
    if configured.is_absolute():
        return configured.resolve()

    return (repo_root / configured).resolve()


def docs_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    default_docs_dir = repo_root / "backend" / "data" / "toolkit_docs"
    raw_docs_dir = _env("DOCS_DIR")
    if not raw_docs_dir:
        return default_docs_dir.resolve()

    configured = Path(raw_docs_dir).expanduser()
    if configured.is_absolute():
        return configured.resolve()

    return (repo_root / configured).resolve()


def _docs_url(local_path: str | None) -> str | None:
    if not local_path:
        return None
    name = Path(local_path).name
    if not name:
        return None
    _ = docs_dir() / name
    return f"/docs/{quote(name)}"


def _citation_url(raw_url: str | None, local_path: str | None) -> str:
    if raw_url:
        if raw_url.startswith("local:"):
            return f"/docs/{quote(raw_url.replace('local:', '', 1))}"
        return raw_url
    return _docs_url(local_path) or ""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/docs/{file_path:path}")
def serve_docs(file_path: str):
    if ".." in Path(file_path).parts:
        raise HTTPException(status_code=400, detail="Invalid path")

    root = docs_dir()
    resolved = (root / file_path).resolve()
    if not str(resolved).startswith(str(root.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=str(resolved))


@app.post("/ask")
def ask(payload: AskRequest) -> dict[str, object]:
    idx_dir = index_dir()
    index_file = idx_dir / "faiss.index"
    meta_file = idx_dir / "meta.json"

    if not meta_file.exists():
        raise HTTPException(
            status_code=503,
            detail=f"RAG index missing. Build it first. Looked for: {meta_file}",
        )
    if not index_file.exists():
        raise HTTPException(
            status_code=503,
            detail=f"RAG index missing. Build it first. Looked for: {index_file}",
        )

    openai_api_key = _env("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="Missing OPENAI_API_KEY. Set it in the environment before calling /ask.",
        )

    llm_model = _env("LLM_MODEL", "gpt-4o-mini")
    embedding_model = _env("EMBEDDING_MODEL", "text-embedding-3-small")

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
            api_key=openai_api_key,
            embedding_model=embedding_model,
        )

        answer = generate_grounded_answer(
            api_key=openai_api_key,
            model=llm_model,
            question=payload.question,
            evidence=evidence,
        )

        citations = [
            {
                "title": item.title,
                "url": _citation_url(item.url, item.local_path),
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
