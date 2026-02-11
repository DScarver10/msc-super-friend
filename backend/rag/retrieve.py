from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
from openai import OpenAI

from .openai_embeddings import embed_query
from .vectors import ChunkRecord, LocalFaissVectorStore


@dataclass
class Evidence:
    evid_id: str
    score: float
    title: str
    excerpt: str
    source_type: str
    source_id: str
    url: str | None = None
    local_path: str | None = None
    page: int | None = None
    section: str | None = None
    subsection: str | None = None
    pub: str | None = None
    domain: str | None = None
    doc_type: str | None = None
    effective_date: str | None = None


@dataclass
class RetrievalTrace:
    query: str
    normalized_query: str
    routed_domain: str
    top_k: int
    candidate_count: int
    vector_weight: float
    lexical_weight: float
    rerank_mode: str
    selected: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "normalized_query": self.normalized_query,
            "routed_domain": self.routed_domain,
            "top_k": self.top_k,
            "candidate_count": self.candidate_count,
            "vector_weight": self.vector_weight,
            "lexical_weight": self.lexical_weight,
            "rerank_mode": self.rerank_mode,
            "selected": self.selected,
        }


@dataclass
class _Candidate:
    rec: ChunkRecord
    vector_score: float = 0.0
    lexical_score: float = 0.0
    rerank_score: float = 0.0
    combined_score: float = 0.0


_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-]{1,}")
_POLICY_RE = re.compile(r"\b(?:AFI|DAFI|AFMAN|DAFMAN|DHA-PI|DHAI)\s*(\d{1,2})\s*[- ]\s*(\d{2,4}(?:\.\d+)?)\b", re.IGNORECASE)
_PUB_RE = re.compile(r"\b(?:AFI|DAFI|AFMAN|DAFMAN|DHA-PI|DHAI|JTR)\s*\d{1,2}-\d{2,4}(?:\.\d+)?\b", re.IGNORECASE)

_ACRONYM_EXPANSIONS = {
    "gpm": "group practice management",
    "topa": "tricare operations and patient administration",
    "meprs": "medical expense and performance reporting system",
    "rmo": "resource management office",
    "mtf": "medical treatment facility",
    "dmlss": "defense medical logistics standard support",
    "umd": "unit manpower document",
}


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


def _normalize_policy_refs(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        prefix = match.group(0).split()[0].upper()
        return f"{prefix} {match.group(1)}-{match.group(2)}"

    return _POLICY_RE.sub(repl, text)


def _normalize_query(question: str) -> str:
    q = _normalize_policy_refs((question or "").strip())
    tokens = _tokenize(q)
    expansions = [_ACRONYM_EXPANSIONS[t] for t in tokens if t in _ACRONYM_EXPANSIONS]
    if expansions:
        q = f"{q} {' '.join(expansions)}"
    return q.strip()


def _route_domain(question: str) -> str:
    text = question.lower()
    if any(k in text for k in ["materiel", "logistics", "dmlss", "supply", "inventory", "medlog"]):
        return "med_log"
    if any(k in text for k in ["access", "referral", "empanel", "tricare", "beneficiary", "appointment"]):
        return "access_to_care"
    if any(k in text for k in ["manpower", "umd", "position", "classification", "hiring"]):
        return "manpower"
    if any(k in text for k in ["dress", "groom", "leadership", "conduct", "morale", "customs", "courtesies"]):
        return "leadership"
    if any(k in text for k in ["quality", "peer review", "patient safety", "adverse event", "credentialing"]):
        return "quality"
    if any(k in text for k in ["facility", "disaster", "fire safety", "mass casualty", "emergency management"]):
        return "facilities"
    return "general"


def _normalize_scores(candidates: list[_Candidate], attr: str) -> None:
    values = [getattr(c, attr) for c in candidates]
    if not values:
        return
    lo = min(values)
    hi = max(values)
    if math.isclose(lo, hi):
        for cand in candidates:
            setattr(cand, attr, 1.0 if hi > 0 else 0.0)
        return
    span = hi - lo
    for cand in candidates:
        setattr(cand, attr, (getattr(cand, attr) - lo) / span)


def _lexical_score(query_tokens: set[str], rec: ChunkRecord) -> float:
    if not query_tokens:
        return 0.0
    title_tokens = set(_tokenize(rec.title))
    text_tokens = set(_tokenize(rec.text))
    overlap_title = len(query_tokens & title_tokens)
    overlap_text = len(query_tokens & text_tokens)
    return (0.7 * overlap_title / max(1, len(query_tokens))) + (0.3 * overlap_text / max(1, len(query_tokens)))


def _is_doctrine(rec: ChunkRecord) -> bool:
    if rec.pub and _PUB_RE.search(rec.pub):
        return True
    title = rec.title or ""
    return bool(_PUB_RE.search(title))


def _is_toolkit_guide(rec: ChunkRecord) -> bool:
    t = (rec.title or "").lower()
    return any(k in t for k in ["mentor guide", "accession guide"])


def _metadata_filter(rec: ChunkRecord, routed_domain: str) -> bool:
    if routed_domain == "general":
        return True
    rec_domain = (rec.domain or "").strip().lower()
    if rec_domain and rec_domain == routed_domain:
        return True
    # Allow doctrine content even if domain inference is imperfect.
    return _is_doctrine(rec)


def _apply_metadata_weight(question: str, rec: ChunkRecord, score: float, routed_domain: str) -> float:
    weighted = score
    if _is_doctrine(rec):
        weighted += 0.20
    if _is_toolkit_guide(rec):
        weighted -= 0.15
    if routed_domain != "general" and (rec.domain or "") == routed_domain:
        weighted += 0.08

    # Policy-ref match boost.
    refs = {m.group(0).upper().replace(" ", "") for m in _PUB_RE.finditer(question)}
    if refs:
        title_norm = (rec.title or "").upper().replace(" ", "")
        for ref in refs:
            if ref in title_norm:
                weighted += 0.20
                break
    return weighted


def _llm_rerank(
    api_key: str,
    question: str,
    candidates: list[_Candidate],
    max_candidates: int = 12,
) -> list[_Candidate]:
    trimmed = candidates[:max_candidates]
    if not trimmed:
        return candidates

    client = OpenAI(api_key=api_key)
    options = "\n".join(
        [f"{i+1}. {c.rec.title} | {c.rec.section or 'no-section'} | {(c.rec.text or '')[:350]}" for i, c in enumerate(trimmed)]
    )
    prompt = (
        "Rank the following chunks by relevance to the question for policy-grounded retrieval.\n"
        "Return ONLY comma-separated item numbers in descending relevance, e.g., '3,1,2'.\n\n"
        f"QUESTION:\n{question}\n\n"
        f"CANDIDATES:\n{options}"
    )
    try:
        resp = client.chat.completions.create(
            model=os.getenv("RAG_RERANK_LLM_MODEL", "gpt-4o-mini"),
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = (resp.choices[0].message.content or "").strip()
        order = [int(x.strip()) - 1 for x in raw.split(",") if x.strip().isdigit()]
        ranked = [trimmed[i] for i in order if 0 <= i < len(trimmed)]
        # Append any missed candidates in original order.
        seen = {id(c) for c in ranked}
        ranked.extend([c for c in trimmed if id(c) not in seen])
        return ranked + candidates[max_candidates:]
    except Exception:
        return candidates


def _build_candidates(
    store: LocalFaissVectorStore,
    question: str,
    normalized_query: str,
    top_k: int,
    api_key: str,
    embedding_model: str,
    vector_weight: float,
    lexical_weight: float,
    rerank_mode: str,
    routed_domain: str,
) -> list[_Candidate]:
    q_vec = embed_query(api_key=api_key, model=embedding_model, text=normalized_query)
    if q_vec.ndim != 1:
        q_vec = np.asarray(q_vec).reshape(-1)

    vector_hits = store.search(q_vec, top_k=max(top_k * 8, 40))
    _index, meta = store.load()
    by_chunk: dict[str, _Candidate] = {}

    for score, rec in vector_hits:
        if not _metadata_filter(rec, routed_domain=routed_domain):
            continue
        by_chunk[rec.chunk_id] = _Candidate(rec=rec, vector_score=float(score))

    query_tokens = set(_tokenize(normalized_query))
    for rec in meta:
        if not _metadata_filter(rec, routed_domain=routed_domain):
            continue
        lex = _lexical_score(query_tokens, rec)
        if lex <= 0:
            continue
        existing = by_chunk.get(rec.chunk_id)
        if existing:
            existing.lexical_score = max(existing.lexical_score, lex)
        else:
            by_chunk[rec.chunk_id] = _Candidate(rec=rec, lexical_score=lex)

    candidates = list(by_chunk.values())
    _normalize_scores(candidates, "vector_score")
    _normalize_scores(candidates, "lexical_score")

    for cand in candidates:
        base = (vector_weight * cand.vector_score) + (lexical_weight * cand.lexical_score)
        cand.combined_score = _apply_metadata_weight(question, cand.rec, base, routed_domain=routed_domain)
        cand.rerank_score = cand.combined_score

    candidates.sort(key=lambda c: c.combined_score, reverse=True)
    if rerank_mode == "llm":
        candidates = _llm_rerank(api_key=api_key, question=question, candidates=candidates)
    return candidates


def _build_evidence(
    candidates: list[_Candidate],
    top_k: int,
    allowed_sources: Optional[list[str]],
) -> tuple[list[Evidence], list[_Candidate]]:
    selected: list[_Candidate] = []
    for cand in candidates:
        if allowed_sources and cand.rec.source_id not in allowed_sources:
            continue
        selected.append(cand)
        if len(selected) >= top_k:
            break

    evidence: list[Evidence] = []
    for i, cand in enumerate(selected, start=1):
        excerpt = (cand.rec.text or "").strip()
        if len(excerpt) > 900:
            excerpt = excerpt[:900].rstrip() + "..."
        evidence.append(
            Evidence(
                evid_id=f"E{i}",
                score=float(cand.combined_score),
                title=cand.rec.title,
                excerpt=excerpt,
                source_type=cand.rec.source_type,
                source_id=cand.rec.source_id,
                url=cand.rec.url,
                local_path=cand.rec.local_path,
                page=cand.rec.page,
                section=cand.rec.section,
                subsection=cand.rec.subsection,
                pub=cand.rec.pub,
                domain=cand.rec.domain,
                doc_type=cand.rec.doc_type,
                effective_date=cand.rec.effective_date,
            )
        )
    return evidence, selected


def retrieve_with_trace(
    index_dir: Path,
    question: str,
    top_k: int = 5,
    allowed_sources: Optional[list[str]] = None,
    api_key: str | None = None,
    embedding_model: str = "text-embedding-3-small",
    vector_weight: float = 0.7,
    lexical_weight: float = 0.3,
    rerank_mode: str = "heuristic",
) -> tuple[list[Evidence], RetrievalTrace]:
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY for embeddings.")

    store = LocalFaissVectorStore(
        index_path=Path(index_dir) / "faiss.index",
        meta_path=Path(index_dir) / "meta.json",
    )

    normalized_query = _normalize_query(question)
    routed_domain = _route_domain(question)
    candidates = _build_candidates(
        store=store,
        question=question,
        normalized_query=normalized_query,
        top_k=top_k,
        api_key=api_key,
        embedding_model=embedding_model,
        vector_weight=vector_weight,
        lexical_weight=lexical_weight,
        rerank_mode=rerank_mode,
        routed_domain=routed_domain,
    )

    evidence, selected = _build_evidence(candidates, top_k=top_k, allowed_sources=allowed_sources)
    trace = RetrievalTrace(
        query=question,
        normalized_query=normalized_query,
        routed_domain=routed_domain,
        top_k=top_k,
        candidate_count=len(candidates),
        vector_weight=vector_weight,
        lexical_weight=lexical_weight,
        rerank_mode=rerank_mode,
        selected=[
            {
                "evid_id": ev.evid_id,
                "title": ev.title,
                "pub": ev.pub,
                "domain": ev.domain,
                "doc_type": ev.doc_type,
                "source_id": ev.source_id,
                "score": round(ev.score, 4),
                "vector_score": round(cand.vector_score, 4),
                "lexical_score": round(cand.lexical_score, 4),
                "section": ev.section,
                "subsection": ev.subsection,
            }
            for ev, cand in zip(evidence, selected)
        ],
    )
    return evidence, trace


def retrieve(
    index_dir: Path,
    question: str,
    top_k: int = 5,
    allowed_sources: Optional[list[str]] = None,
    api_key: str | None = None,
    embedding_model: str = "text-embedding-3-small",
) -> list[Evidence]:
    evidence, _trace = retrieve_with_trace(
        index_dir=index_dir,
        question=question,
        top_k=top_k,
        allowed_sources=allowed_sources,
        api_key=api_key,
        embedding_model=embedding_model,
    )
    return evidence
