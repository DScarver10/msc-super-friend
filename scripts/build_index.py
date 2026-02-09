from __future__ import annotations

import os
import sys
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

    result = ingest(
        sources_path=sources_path,
        index_dir=index_dir,
        toolkit_docs_dir=toolkit_docs_dir,
        api_key=api_key,
        embedding_model=embedding_model,
    )

    print(f"Index built at {index_dir}")
    print(f"Chunks: {result.num_chunks} | Sources: {len(result.sources)} | Skipped: {len(result.skipped_items)}")


if __name__ == "__main__":
    main()
