from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional


class AskRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    top_k: Optional[int] = Field(default=None, ge=1, le=12)
    allowed_sources: Optional[List[str]] = None


class Citation(BaseModel):
    source: str
    title: str
    url: str
    score: float


class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    grounded: bool
    indexed_as_of: str
