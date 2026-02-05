# backend/rag/ingest.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

import yaml

from .chunking import chunk_text
from .loaders import LoadedDoc, fetch_url_text, load_toolkit_local_docs
from .vectors import ChunkRecord, LocalFaissVectorStore


@dataclass(frozen=True)
class IngestResult:
    indexed_as_of: str
    num_chunks: int
    sources: List[str]
    skipped_items: int


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _load_sources_yaml(sources_path: str) -> list[dict]:
    p = Path(sources_path)
    if not p.exists():
        return []
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return data.get("sources", []) or []


def ingest(sources_path: str, index_dir: str, toolkit_docs_dir: str) -> IngestResult:
    """
    Builds a FAISS index from:
      - web sources defined in sources.yaml (existing behavior)
      - local toolkit docs under backend/data/toolkit_docs (new)
    """
    index_path = Path(index_dir)
    index_path.mkdir(parents=True, exist_ok=True)

    store = LocalFaissVectorStore(index_path)

    loaded_docs: List[LoadedDoc] = []
    print("INGEST: starting ingestion")
    skipped = 0

    # --- Web sources ---
    for src in _load_sources_yaml(sources_path):
        url = (src.get("url") or "").strip()
        title = (src.get("title") or url).strip()
        source_name = (src.get("source") or "web").strip()

        if not url:
            skipped += 1
            continue

        try:
            html = fetch_url_text(url)
            loaded_docs.append(LoadedDoc(title=title, source=source_name, url=url, text=html))
            print(f"INGEST: loaded web doc '{title}' ({len(html)} chars)")
        except Exception:
            skipped += 1

    # --- Local toolkit docs ---
    toolkit_dir = Path(toolkit_docs_dir)
    toolkit_docs = load_toolkit_local_docs(Path(toolkit_docs_dir))
    print(f"INGEST: loaded {len(toolkit_docs)} local toolkit docs")
    loaded_docs.extend(toolkit_docs)

    # --- Chunk + embed ---
    all_chunks: List[ChunkRecord] = []
    for d in loaded_docs:
        for i, chunk in enumerate(chunk_text(d.text)):
            all_chunks.append(
                ChunkRecord(
                    chunk_id=f"{d.source}:{d.title}:{i}",
                    text=chunk,
                    title=d.title,
                    url=d.url,
                    source=d.source,
                )
            )

    store.rebuild(all_chunks)

    indexed_as_of = _now_iso()
    sources = sorted(list({d.source for d in loaded_docs}))

    return IngestResult(
        indexed_as_of=indexed_as_of,
        num_chunks=len(all_chunks),
        sources=sources,
        skipped_items=skipped,
    )
