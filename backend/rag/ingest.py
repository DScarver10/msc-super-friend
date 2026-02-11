# backend/rag/ingest.py
from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np

from .chunking import chunk_policy_text
from .loaders import load_sources
from .openai_embeddings import embed_texts
from .vectors import ChunkRecord, LocalFaissVectorStore


@dataclass
class IngestResult:
    indexed_as_of: str
    num_chunks: int
    sources: List[str]
    skipped_items: List[dict]


PUB_RE = re.compile(r"\b(?:AFI|DAFI|AFMAN|DAFMAN|DHA-PI|DHAI|JTR)\s*\d{1,2}-\d{2,4}(?:\.\d+)?\b", re.IGNORECASE)
DATE_RE = re.compile(r"\b(?:\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}|\d{4})\b")


def _now_iso() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


def _stable_chunk_id(source_id: str, chunk_index: int, text: str) -> str:
    h = hashlib.sha1(f"{source_id}|{chunk_index}|{text}".encode("utf-8")).hexdigest()[:16]
    return f"{source_id}-{chunk_index}-{h}"


def _infer_pub(title: str, source_id: str) -> str | None:
    for field in (title, source_id):
        match = PUB_RE.search(field or "")
        if match:
            return match.group(0).upper()
    return None


def _infer_doc_type(title: str) -> str:
    t = (title or "").lower()
    if "guide" in t:
        return "guide"
    if "policy" in t:
        return "policy"
    if "reference" in t:
        return "reference"
    if "faq" in t:
        return "faq"
    return "publication"


def _infer_domain(title: str, source_id: str) -> str:
    text = f"{title} {source_id}".lower()
    if any(k in text for k in ["logistics", "materiel", "medlog", "dmlss"]):
        return "med_log"
    if any(k in text for k in ["tricare", "patient administration", "access", "referral", "empanel"]):
        return "access_to_care"
    if any(k in text for k in ["manpower", "position", "umd", "force structure"]):
        return "manpower"
    if any(k in text for k in ["dress", "leadership", "morale", "conduct", "pme"]):
        return "leadership"
    if any(k in text for k in ["quality", "peer review", "patient safety", "risk management"]):
        return "quality"
    if any(k in text for k in ["facility", "disaster", "emergency", "fire safety"]):
        return "facilities"
    return "general"


def _infer_effective_date(title: str, text: str) -> str | None:
    for field in (title, text[:3000]):
        match = DATE_RE.search(field or "")
        if match:
            return match.group(0)
    return None


def ingest(
    sources_path: Path,
    index_dir: Path,
    toolkit_docs_dir: Optional[Path] = None,
    api_key: Optional[str] = None,
    embedding_model: str = "text-embedding-3-small",
    chunk_chars: int = 1200,
    chunk_overlap: int = 180,
) -> IngestResult:
    sources_path = Path(sources_path)
    index_dir = Path(index_dir)
    toolkit_docs_dir = Path(toolkit_docs_dir) if toolkit_docs_dir else None

    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY for ingestion embeddings.")

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
            text = (item.get("text") or "").strip()

            source_ids.append(source_id)
            if not text:
                skipped.append({"source_id": source_id, "reason": "empty_text"})
                continue

            pub = _infer_pub(title=title, source_id=source_id)
            domain = _infer_domain(title=title, source_id=source_id)
            doc_type = _infer_doc_type(title=title)
            effective_date = _infer_effective_date(title=title, text=text)

            pieces = chunk_policy_text(text=text, chunk_size=chunk_chars, overlap=chunk_overlap)
            for i, piece in enumerate(pieces):
                chunk_text = piece.text.strip()
                if not chunk_text:
                    continue

                chunk_id = _stable_chunk_id(source_id, i, chunk_text)
                rec = ChunkRecord(
                    chunk_id=chunk_id,
                    source_id=source_id,
                    source_type=source_type,
                    title=title,
                    text=chunk_text,
                    url=url,
                    local_path=local_path,
                    page=page,
                    chunk_index=i,
                    section=piece.section,
                    subsection=piece.subsection,
                    pub=pub,
                    domain=domain,
                    doc_type=doc_type,
                    effective_date=effective_date,
                )
                all_records.append(rec)
                all_texts.append(chunk_text)
        except Exception as exc:
            skipped.append({"source_id": item.get("source_id") or item.get("title"), "reason": str(exc)})

    if not all_texts:
        raise RuntimeError("No vectors generated (no chunkable text found).")

    vectors = embed_texts(api_key=api_key, model=embedding_model, texts=all_texts)
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim != 2 or vectors.shape[0] != len(all_records):
        raise RuntimeError(
            f"Embedding shape mismatch. vectors={getattr(vectors, 'shape', None)} records={len(all_records)}"
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
