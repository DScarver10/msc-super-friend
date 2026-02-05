from __future__ import annotations

import os
from typing import List

import numpy as np
from openai import OpenAI


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not set. Add it to your environment or .env file."
        )
    return OpenAI(api_key=api_key)


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Generate embeddings for a list of texts using OpenAI.

    Returns:
        np.ndarray of shape (N, D) with dtype float32
    """
    if not texts:
        return np.empty((0, 0), dtype=np.float32)

    client = _get_client()

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )

    vectors = [item.embedding for item in response.data]
    return np.array(vectors, dtype=np.float32)
