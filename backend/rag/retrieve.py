from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np

from .vectors import ChunkRecord, LocalFaissVectorStore

# If you already have an embeddings helper, keep its function name consistent.
# This assumes you have: embed_query(api_key: str, model: str, text: str) -> np.ndarray
from .openai_embeddings import embed_query  # type: ignore


@dataclass
class Evidence:
    evid_id: str      # "E1", "E2", ...
    score: float
    title: str
    excerpt: str
    source_type: str
    source_id: str
    url: str | None = None
    local_path: str | None = None
    page: int | None = None


def retrieve(
    index_dir: Path,
    question: str,
    top_k: int = 5,
    allowed_sources: Optional[List[str]] = None,
    api_key: str | None = None,
    embedding_model: str = "text-embedding-3-small",
) -> List[Evidence]:
    index_dir = Path(index_dir)

    store = LocalFaissVectorStore(
        index_path=index_dir / "faiss.index",
        meta_path=index_dir / "meta.json",
    )

    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY for embeddings.")

    q_vec = embed_query(api_key=api_key, model=embedding_model, text=question)
    if q_vec.ndim != 1:
        q_vec = np.asarray(q_vec).reshape(-1)

    results = store.search(q_vec, top_k=top_k)

    evidence: List[Evidence] = []
    k = 0
    for score, rec in results:
        if allowed_sources and rec.source_id not in allowed_sources:
            continue

        k += 1
        evid_id = f"E{k}"
        excerpt = rec.text.strip()
        if len(excerpt) > 900:
            excerpt = excerpt[:900].rstrip() + "…"

        evidence.append(
            Evidence(
                evid_id=evid_id,
                score=score,
                title=rec.title,
                excerpt=excerpt,
                source_type=rec.source_type,
                source_id=rec.source_id,
                url=rec.url,
                local_path=rec.local_path,
                page=rec.page,
            )
        )

    return evidence
