from __future__ import annotations

import os
import sys
import json
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.rag.ingest import ingest


def resolve_toolkit_docs_dir(root: Path) -> Path:
    env_value = os.getenv("TOOLKIT_DOCS_DIR", "").strip()
    if env_value:
        return Path(env_value).resolve()

    preferred = root / "backend" / "toolkit_docs"
    if preferred.exists():
        return preferred

    fallback = root / "backend" / "data" / "toolkit_docs"
    return fallback


def main() -> None:
    load_dotenv(dotenv_path=ROOT / ".env")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("Missing OPENAI_API_KEY. Set it in environment or .env before building the index.")

    sources_path = Path(os.getenv("SOURCES_PATH", str(ROOT / "backend" / "data" / "sources.yaml"))).resolve()
    index_dir = Path(os.getenv("INDEX_DIR", str(ROOT / "backend" / "data" / "index"))).resolve()
    toolkit_docs_dir = resolve_toolkit_docs_dir(ROOT)
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip()
    chunk_chars = int(os.getenv("CHUNK_CHARS", "1200").strip() or "1200")
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "180").strip() or "180")

    result = ingest(
        sources_path=sources_path,
        index_dir=index_dir,
        toolkit_docs_dir=toolkit_docs_dir,
        api_key=api_key,
        embedding_model=embedding_model,
        chunk_chars=chunk_chars,
        chunk_overlap=chunk_overlap,
    )

    print(f"Index built at {index_dir}")
    print(
        f"Chunks: {result.num_chunks} | Sources: {len(result.sources)} | "
        f"Skipped: {len(result.skipped_items)} | Chunk chars: {chunk_chars} | Overlap: {chunk_overlap}"
    )

    meta_path = index_dir / "meta.json"
    if not meta_path.exists():
        raise SystemExit(f"Missing expected metadata file: {meta_path}")

    rows = json.loads(meta_path.read_text(encoding="utf-8"))
    grouped: dict[tuple[str, str], int] = defaultdict(int)
    for row in rows:
        title = str(row.get("title") or "unknown").strip()
        local_path = str(row.get("local_path") or "-").strip()
        grouped[(title, local_path)] += 1

    print("\nSummary by publication")
    print("| publication | local path | number of chunks generated |")
    print("|---|---|---:|")
    for (title, local_path), count in sorted(grouped.items(), key=lambda kv: kv[0][0].lower()):
        print(f"| {title} | {local_path} | {count} |")


if __name__ == "__main__":
    main()
