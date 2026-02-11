from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np

try:
    import faiss  # type: ignore
except Exception as e:
    raise RuntimeError(
        "faiss is required. Install faiss-cpu (or ensure it's in requirements)."
    ) from e


@dataclass
class ChunkRecord:
    """
    Metadata for a single embedded chunk.

    Keep this stable: ingest writes this, retrieve reads this.
    """
    chunk_id: str
    source_id: str
    source_type: str  # "web" | "file"
    title: str
    text: str

    url: str | None = None
    local_path: str | None = None
    page: int | None = None
    chunk_index: int | None = None
    section: str | None = None
    subsection: str | None = None
    pub: str | None = None
    domain: str | None = None
    doc_type: str | None = None
    effective_date: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "ChunkRecord":
        return ChunkRecord(**d)


class LocalFaissVectorStore:
    """
    Minimal FAISS store:
      - index at index_path (faiss index)
      - meta at meta_path   (json list[ChunkRecord])
    """

    def __init__(self, index_path: Path, meta_path: Path):
        self.index_path = Path(index_path)
        self.meta_path = Path(meta_path)

    def save(self, vectors: np.ndarray, meta: List[ChunkRecord]) -> None:
        if vectors.ndim != 2:
            raise ValueError("vectors must be 2D: shape (N, D)")
        if len(meta) != vectors.shape[0]:
            raise ValueError("meta length must match vectors rows")
        if vectors.dtype != np.float32:
            vectors = vectors.astype(np.float32)

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)

        dim = int(vectors.shape[1])
        index = faiss.IndexFlatIP(dim)  # inner product; normalize vectors if you want cosine
        index.add(vectors)

        faiss.write_index(index, str(self.index_path))

        raw = [m.to_dict() for m in meta]
        self.meta_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> Tuple["faiss.Index", List[ChunkRecord]]:
        if not self.index_path.exists() or not self.meta_path.exists():
            raise FileNotFoundError(
                f"Index not found. Expected:\n- {self.index_path}\n- {self.meta_path}"
            )

        index = faiss.read_index(str(self.index_path))
        raw = json.loads(self.meta_path.read_text(encoding="utf-8"))
        meta = [ChunkRecord.from_dict(item) for item in raw]
        return index, meta

    def search(self, query_vec: np.ndarray, top_k: int) -> List[Tuple[float, ChunkRecord]]:
        index, meta = self.load()

        if query_vec.ndim == 1:
            query_vec = query_vec.reshape(1, -1)
        if query_vec.dtype != np.float32:
            query_vec = query_vec.astype(np.float32)

        scores, idxs = index.search(query_vec, int(top_k))

        results: List[Tuple[float, ChunkRecord]] = []
        for score, i in zip(scores[0], idxs[0]):
            if i == -1:
                continue
            results.append((float(score), meta[int(i)]))
        return results
