from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.rag.openai_embeddings import embed_query
from backend.rag.vectors import ChunkRecord, LocalFaissVectorStore


@dataclass
class Evidence:
    rec: ChunkRecord
    score: float


@dataclass
class AnswerRow:
    qid: int
    question: str
    answer: str
    citations: List[str]
    status: str
    notes: str


PUB_RE = re.compile(
    r"\b(?:AFI|DAFI|AFMAN|DAFMAN|DHA-PI|DHAI|DHA|JTR)\s*\d{1,2}-\d{2,4}(?:\.\d+)?\b",
    re.IGNORECASE,
)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
DENY_PATTERNS = [
    "msc mentor guide",
]


def _load_questions(path: Path) -> List[str]:
    raw = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in raw if line.strip()]


def _filter_banned(rec: ChunkRecord) -> bool:
    hay = " ".join([rec.title or "", rec.local_path or "", rec.url or ""]).lower()
    return any(pat in hay for pat in DENY_PATTERNS)


def _extract_pub(title: str, source_id: str) -> str:
    for field in (title, source_id):
        if not field:
            continue
        match = PUB_RE.search(field)
        if match:
            return match.group(0).upper()
    return title.strip() or source_id.strip() or "UNKNOWN"


def _closest_heading(text: str) -> str:
    for line in (text or "").splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned[:120]
    return "excerpt"


def _format_citation(rec: ChunkRecord) -> str:
    pub = _extract_pub(rec.title, rec.source_id)
    title = rec.title.strip() if rec.title else pub
    source = rec.local_path or rec.url or "unknown_source"
    if rec.page is not None:
        locator = f"p.{rec.page}"
    else:
        heading = _closest_heading(rec.text)
        locator = f"section.{heading}"
    return f"{pub} â€” {title} â€” {locator} â€” {source}"


def _professional_insufficient_answer(question: str, evidence: List[Evidence]) -> str:
    if evidence:
        refs = [_extract_pub(ev.rec.title, ev.rec.source_id) for ev in evidence[:2]]
        unique_refs = ", ".join(dict.fromkeys(refs))
        return (
            "A definitive answer is not supported by the currently indexed sources for this question. "
            f"The most relevant material reviewed was from {unique_refs}. "
            "Please confirm the governing instruction in official publication repositories "
            "or with your functional authority before taking action."
        )
    return (
        "A definitive answer is not supported by the currently indexed sources for this question. "
        "Please confirm the governing instruction in official publication repositories "
        "or with your functional authority before taking action."
    )

def _select_evidence(
    store: LocalFaissVectorStore,
    question: str,
    api_key: str,
    embedding_model: str,
    top_k: int,
    min_score: float,
) -> List[Evidence]:
    q_vec = embed_query(api_key=api_key, model=embedding_model, text=question)
    results = store.search(q_vec, top_k=top_k)
    evidence: List[Evidence] = []
    for score, rec in results:
        if _filter_banned(rec):
            continue
        evidence.append(Evidence(rec=rec, score=float(score)))
    return [ev for ev in evidence if ev.score >= min_score]


def _extract_answer(evidence: List[Evidence]) -> Tuple[str, List[Evidence]]:
    if not evidence:
        return "", []

    sentences: List[str] = []
    used: List[Evidence] = []
    for ev in evidence:
        chunk_sentences = [s.strip() for s in SENTENCE_RE.split(ev.rec.text or "") if s.strip()]
        for sent in chunk_sentences:
            if len(sent) < 20:
                continue
            sentences.append(sent)
            if ev not in used:
                used.append(ev)
            if len(sentences) >= 6:
                break
        if len(sentences) >= 6:
            break

    if len(sentences) < 3:
        return "", []

    return " ".join(sentences[:6]), used


def _build_row_from_evidence(qid: int, question: str, evidence: List[Evidence]) -> AnswerRow:
    answer, used = _extract_answer(evidence)
    if not answer:
        return AnswerRow(
            qid=qid,
            question=question,
            answer=_professional_insufficient_answer(question, evidence),
            citations=[],
            status="INSUFFICIENT_EVIDENCE",
            notes="No sufficiently relevant chunks or not enough extractable sentences.",
        )

    citations = [_format_citation(ev.rec) for ev in used[:3]]
    if not citations:
        return AnswerRow(
            qid=qid,
            question=question,
            answer=_professional_insufficient_answer(question, evidence),
            citations=[],
            status="INSUFFICIENT_EVIDENCE",
            notes="Retrieved text did not produce verifiable citations.",
        )

    return AnswerRow(
        qid=qid,
        question=question,
        answer=answer,
        citations=citations,
        status="OK",
        notes="Extracted from top-ranked chunks.",
    )


def answer_questions(
    questions: Iterable[str],
    index_dir: Path,
    api_key: str,
    embedding_model: str,
    top_k: int,
    min_score: float,
) -> List[AnswerRow]:
    store = LocalFaissVectorStore(
        index_path=index_dir / "faiss.index",
        meta_path=index_dir / "meta.json",
    )

    rows: List[AnswerRow] = []
    for idx, question in enumerate(questions, start=1):
        evidence = _select_evidence(store, question, api_key, embedding_model, top_k, min_score)
        rows.append(_build_row_from_evidence(idx, question, evidence))
    return rows


def _write_csv(path: Path, rows: List[AnswerRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "question", "answer", "citations", "status", "notes"])
        for row in rows:
            writer.writerow(
                [
                    row.qid,
                    row.question,
                    row.answer,
                    "; ".join(row.citations),
                    row.status,
                    row.notes,
                ]
            )


def _print_insufficient(rows: List[AnswerRow]) -> None:
    insufficient = [row for row in rows if row.status == "INSUFFICIENT_EVIDENCE"]
    print(f"Questions with INSUFFICIENT_EVIDENCE: {len(insufficient)}")
    for row in insufficient:
        print(f"{row.qid}. {row.question}")


def _ensure_index(index_dir: Path) -> None:
    index_file = index_dir / "faiss.index"
    meta_file = index_dir / "meta.json"
    if not index_file.exists() or not meta_file.exists():
        print(
            "RAG index not found. Build it with:\n"
            "  python scripts/build_index.py\n"
            f"Expected files:\n  {index_file}\n  {meta_file}",
            file=sys.stderr,
        )
        raise SystemExit(2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Answer doctrine questions using the local RAG index.")
    parser.add_argument("--in", dest="in_path", default="scripts/questions.txt", help="Path to questions file.")
    parser.add_argument("--out", dest="out_path", default="scripts/answers.csv", help="Path to output CSV.")
    parser.add_argument("--top-k", dest="top_k", type=int, default=8)
    parser.add_argument("--min-score", dest="min_score", type=float, default=0.2)
    args = parser.parse_args()

    load_dotenv()
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise SystemExit("Missing OPENAI_API_KEY. Set it in environment or .env before running.")

    index_dir = Path(os.getenv("INDEX_DIR", "backend/data/index")).resolve()
    _ensure_index(index_dir)

    embedding_model = (os.getenv("EMBEDDING_MODEL") or "text-embedding-3-small").strip()
    questions_path = Path(args.in_path)
    if not questions_path.exists():
        raise SystemExit(f"Missing questions file: {questions_path}")

    questions = _load_questions(questions_path)
    if not questions:
        raise SystemExit("No questions found.")

    rows = answer_questions(
        questions=questions,
        index_dir=index_dir,
        api_key=api_key,
        embedding_model=embedding_model,
        top_k=args.top_k,
        min_score=args.min_score,
    )
    _write_csv(Path(args.out_path), rows)
    _print_insufficient(rows)
    print(f"Wrote {len(rows)} rows to {args.out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

