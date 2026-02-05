from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import json
import numpy as np


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    text: str
    title: str
    url: str
    source: str


class LocalFaissVectorStore:
    """
    Simple local FAISS vector store.

    Files created inside index_dir:
      - index.faiss
      - meta.json
    """

    def __init__(self, index_dir: Path):
        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.index_dir / "index.faiss"
        self.meta_path = self.index_dir / "meta.json"

        self._index = None
        self._meta: List[ChunkRecord] = []

    def rebuild(self, chunks: List[ChunkRecord]) -> None:
        try:
            import faiss  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "Missing dependency faiss-cpu. Install with: pip install faiss-cpu"
            ) from e

        from backend.rag.openai_embeddings import embed_texts

        texts = [c.text for c in chunks]
        vectors = embed_texts(texts)

        if len(vectors) == 0:
            raise RuntimeError("No vectors generated")

        dim = vectors.shape[1]
        index = faiss.IndexFlatIP(dim)
        faiss.normalize_L2(vectors)
        index.add(vectors)

        faiss.write_index(index, str(self.index_path))

        with self.meta_path.open("w", encoding="utf-8") as f:
            json.dump([c.__dict__ for c in chunks], f, indent=2)

        self._index = index
        self._meta = chunks

    def search(self, query: str, k: int = 5) -> List[Tuple[ChunkRecord, float]]:
        try:
            import faiss  # type: ignore
        except Exception:
            return []

        from backend.rag.openai_embeddings import embed_texts

        if self._index is None:
            if not self.index_path.exists():
                return []
            self._index = faiss.read_index(str(self.index_path))
            with self.meta_path.open("r", encoding="utf-8") as f:
                self._meta = [ChunkRecord(**x) for x in json.load(f)]

        q = embed_texts([query])
        faiss.normalize_L2(q)

        scores, idxs = self._index.search(q, k)

        results: List[Tuple[ChunkRecord, float]] = []
        for score, idx in zip(scores[0], idxs[0]):
            if 0 <= idx < len(self._meta):
                results.append((self._meta[idx], float(score)))
        return results

