from __future__ import annotations

import os
from typing import List, Optional

import numpy as np
from openai import OpenAI


def _get_client(api_key: Optional[str] = None) -> OpenAI:
    resolved_key = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved_key:
        raise RuntimeError(
            "OPENAI_API_KEY not set. Add it to your environment or .env file."
        )
    return OpenAI(api_key=resolved_key)


def _embed_texts_with_client(client: OpenAI, model: str, texts: List[str]) -> np.ndarray:
    if not texts:
        return np.empty((0, 0), dtype=np.float32)

    # Keep each request below model token-per-request limits by batching inputs.
    # Approximation: 1 token ~= 4 chars for mixed English/policy text.
    max_batch_tokens = 220_000
    max_batch_items = 64
    max_batch_chars = max_batch_tokens * 4

    vectors: list[list[float]] = []
    batch: list[str] = []
    batch_chars = 0

    def flush_batch() -> None:
        nonlocal batch, batch_chars, vectors
        if not batch:
            return
        response = client.embeddings.create(
            model=model,
            input=batch,
        )
        vectors.extend([item.embedding for item in response.data])
        batch = []
        batch_chars = 0

    for text in texts:
        cleaned = (text or "").strip()
        if not cleaned:
            cleaned = " "

        text_chars = len(cleaned)
        if batch and (len(batch) >= max_batch_items or (batch_chars + text_chars) > max_batch_chars):
            flush_batch()

        # If one input is very large, keep the tail but ensure we still embed something deterministic.
        if text_chars > max_batch_chars:
            cleaned = cleaned[:max_batch_chars]
            text_chars = len(cleaned)

        batch.append(cleaned)
        batch_chars += text_chars

    flush_batch()
    return np.array(vectors, dtype=np.float32)


def embed_texts(*args, **kwargs) -> np.ndarray:
    """
    Generate embeddings for a list of texts using OpenAI.

    Supported call patterns:
      - embed_texts(texts: List[str])
      - embed_texts(api_key: str, model: str, texts: List[str])

    Returns:
        np.ndarray of shape (N, D) with dtype float32
    """
    if kwargs:
        api_key = kwargs.get("api_key")
        model = kwargs.get("model", "text-embedding-3-small")
        texts = kwargs.get("texts")
        if texts is None:
            raise TypeError("embed_texts() missing required argument: 'texts'")
        client = _get_client(api_key=api_key)
        return _embed_texts_with_client(client, model, texts)

    if len(args) == 1:
        texts = args[0]
        client = _get_client()
        return _embed_texts_with_client(client, "text-embedding-3-small", texts)
    if len(args) == 3:
        api_key, model, texts = args
        client = _get_client(api_key=api_key)
        return _embed_texts_with_client(client, model, texts)

    raise TypeError(
        "embed_texts() expects (texts) or (api_key, model, texts)"
    )


def embed_query(api_key: str, model: str, text: str) -> np.ndarray:
    """
    Thin adapter to embed a single query string.
    """
    vectors = embed_texts(api_key=api_key, model=model, texts=[text])
    if vectors.ndim == 2 and vectors.shape[0] == 1:
        return vectors[0]
    return np.asarray(vectors).reshape(-1)
