# backend/rag/ingest.py
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
import numpy as np

from .chunking import chunk_text
from .loaders import load_sources  # expects: load_sources(sources_path, toolkit_docs_dir) -> list[dict]
from .vectors import ChunkRecord, LocalFaissVectorStore

# This assumes: embed_texts(api_key: str, model: str, texts: list[str]) -> np.ndarray (N,D)
from .openai_embeddings import embed_texts  # type: ignore


@dataclass
class IngestResult:
    indexed_as_of: str
    num_chunks: int
    sources: List[str]
    skipped_items: List[dict]


def _now_iso() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


def _stable_chunk_id(source_id: str, chunk_index: int, text: str) -> str:
    h = hashlib.sha1(f"{source_id}|{chunk_index}|{text}".encode("utf-8")).hexdigest()[:16]
    return f"{source_id}-{chunk_index}-{h}"


def ingest(
    sources_path: Path,
    index_dir: Path,
    toolkit_docs_dir: Optional[Path] = None,
    api_key: Optional[str] = None,
    embedding_model: str = "text-embedding-3-small",
    chunk_chars: int = 1400,
    chunk_overlap: int = 150,
) -> IngestResult:
    sources_path = Path(sources_path)
    index_dir = Path(index_dir)
    toolkit_docs_dir = Path(toolkit_docs_dir) if toolkit_docs_dir else None

    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY for ingestion embeddings.")

    # Load items from YAML + local docs folder
    items = load_sources(sources_path=sources_path, toolkit_docs_dir=toolkit_docs_dir)

    all_records: List[ChunkRecord] = []
    all_texts: List[str] = []
    skipped: List[dict] = []

    source_ids: List[str] = []

    for item in items:
        try:
            source_id = str(item.get("source_id") or item.get("id") or item.get("title") or "unknown").strip()
            source_type = str(item.get("source_type") or "web").strip()
            title = str(item.get("title") or source_id).strip()
            url = item.get("url")
            local_path = item.get("local_path")
            page = item.get("page")

            source_ids.append(source_id)

            text = (item.get("text") or "").strip()
            if not text:
                skipped.append({"source_id": source_id, "reason": "empty_text"})
                continue

            chunks = chunk_text(text, max_chars=chunk_chars, overlap=chunk_overlap)
            for i, ch in enumerate(chunks):
                ch = ch.strip()
                if not ch:
                    continue

                chunk_id = _stable_chunk_id(source_id, i, ch)
                rec = ChunkRecord(
                    chunk_id=chunk_id,
                    source_id=source_id,
                    source_type=source_type,
                    title=title,
                    text=ch,
                    url=url,
                    local_path=local_path,
                    page=page,
                    chunk_index=i,
                )
                all_records.append(rec)
                all_texts.append(ch)

        except Exception as e:
            skipped.append({"source_id": item.get("source_id") or item.get("title"), "reason": str(e)})

    if not all_texts:
        raise RuntimeError("No vectors generated (no chunkable text found).")

    vectors = embed_texts(api_key=api_key, model=embedding_model, texts=all_texts)
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim != 2 or vectors.shape[0] != len(all_records):
        raise RuntimeError(
            f"Embedding shape mismatch. vectors={getattr(vectors,'shape',None)} records={len(all_records)}"
        )

    store = LocalFaissVectorStore(
        index_path=index_dir / "faiss.index",
        meta_path=index_dir / "meta.json",
    )
    store.save(vectors=vectors, meta=all_records)

    return IngestResult(
        indexed_as_of=_now_iso(),
        num_chunks=len(all_records),
        sources=sorted(list(set(source_ids))),
        skipped_items=skipped,
    )
