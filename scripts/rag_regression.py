from __future__ import annotations

import argparse
import json
import os
import statistics
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from backend.rag.llm import generate_grounded_answer
from backend.rag.retrieve import retrieve_with_trace


def _load_cases(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Regression file must contain a JSON array.")
    return [item for item in raw if isinstance(item, dict)]


def _source_recall_at_k(retrieved: list[str], expected: list[str]) -> float | None:
    if not expected:
        return None
    found = len(set(retrieved) & set(expected))
    return found / max(1, len(set(expected)))


def _citations_present(answer: str) -> bool:
    return "[E" in (answer or "")


def run_regression(
    index_dir: Path,
    cases_path: Path,
    top_k: int,
    with_llm: bool,
    embedding_model: str,
    llm_model: str,
) -> int:
    load_dotenv()
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required.")

    cases = _load_cases(cases_path)
    if not cases:
        raise RuntimeError("No regression cases found.")

    recalls: list[float] = []
    passes = 0

    print(f"Running {len(cases)} regression cases (top_k={top_k}, with_llm={with_llm})")

    for idx, case in enumerate(cases, start=1):
        question = str(case.get("question", "")).strip()
        if not question:
            print(f"[{idx}] SKIP: empty question")
            continue

        expected_sources = [str(x) for x in (case.get("expected_sources") or [])]
        evidence, trace = retrieve_with_trace(
            index_dir=index_dir,
            question=question,
            top_k=top_k,
            api_key=api_key,
            embedding_model=embedding_model,
        )

        retrieved_sources = [e.source_id for e in evidence]
        recall = _source_recall_at_k(retrieved_sources, expected_sources)
        if recall is not None:
            recalls.append(recall)

        llm_ok = True
        if with_llm:
            answer = generate_grounded_answer(
                api_key=api_key,
                model=llm_model,
                question=question,
                evidence=evidence,
            )
            llm_ok = _citations_present(answer)

        case_pass = (recall is None or recall > 0.0) and llm_ok
        passes += int(case_pass)

        print(
            f"[{idx}] {'PASS' if case_pass else 'FAIL'} "
            f"recall={('n/a' if recall is None else f'{recall:.2f}')} "
            f"top_source={(retrieved_sources[0] if retrieved_sources else 'none')} "
            f"rewritten_query={trace.rewritten_query!r}"
        )

    avg_recall = statistics.mean(recalls) if recalls else 0.0
    print(f"\nSummary: pass_rate={passes}/{len(cases)} avg_recall={avg_recall:.3f}")
    return 0 if passes == len(cases) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RAG retrieval regression checks.")
    parser.add_argument("--index-dir", default="backend/data/index")
    parser.add_argument("--cases", default="scripts/rag_regression_cases.json")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--with-llm", action="store_true", help="Also evaluate answer citation formatting.")
    parser.add_argument("--embedding-model", default=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    parser.add_argument("--llm-model", default=os.getenv("LLM_MODEL", "gpt-4o-mini"))
    args = parser.parse_args()

    return run_regression(
        index_dir=Path(args.index_dir),
        cases_path=Path(args.cases),
        top_k=args.top_k,
        with_llm=args.with_llm,
        embedding_model=args.embedding_model,
        llm_model=args.llm_model,
    )


if __name__ == "__main__":
    raise SystemExit(main())
