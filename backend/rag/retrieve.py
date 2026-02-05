from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .vectorstore import LocalFaissVectorStore


@dataclass(frozen=True)
class Evidence:
    source: str
    title: str
    url: str
    text: str
    score: float


def retrieve(
    index_dir: Path,
    question: str,
    top_k: int,
    allowed_sources: Optional[List[str]] = None,
) -> List[Evidence]:
    store = LocalFaissVectorStore(
        index_path=index_dir / "faiss.index",
        meta_path=index_dir / "meta.json",
    )

    results = store.query(question, top_k=top_k, allowed_sources=allowed_sources)

    evid: list[Evidence] = []
    for r in results:
        evid.append(
            Evidence(
                source=str(r.get("source", "")),
                title=str(r.get("title", "")),
                url=str(r.get("url", "")),
                text=str(r.get("text", "")),
                score=float(r.get("score", 0.0)),
            )
        )
    return evid


def is_grounded_enough(evidence: List[Evidence], min_score: float = 0.20) -> bool:
    """
    Heuristic threshold for whether retrieval looks usable.
    With normalized embeddings + inner product, scores are typically 0..1-ish.
    You will tune this later.
    """
    if not evidence:
        return False
    return max(e.score for e in evidence) >= min_score
