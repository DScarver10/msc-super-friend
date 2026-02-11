from __future__ import annotations
from dotenv import load_dotenv

from dataclasses import dataclass
from pathlib import Path
import os


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v or not v.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return v.strip()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    llm_model: str
    sources_path: str
    index_dir: str
    toolkit_docs_dir: str
    docs_dir: str
    app_version: str


def load_settings() -> Settings:
    load_dotenv()
    root = Path(__file__).resolve().parents[1]

    return Settings(
        openai_api_key=_require_env("OPENAI_API_KEY"),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini").strip(),
        sources_path=os.getenv(
            "SOURCES_PATH", str(root / "backend" / "data" / "sources.yaml")
        ).strip(),
        index_dir=os.getenv(
            "INDEX_DIR", str(root / "backend" / "data" / "index")
        ).strip(),
        toolkit_docs_dir=os.getenv(
            "TOOLKIT_DOCS_DIR", str(root / "backend" / "data" / "toolkit_docs")
        ).strip(),
        docs_dir=os.getenv("DOCS_DIR", str(root / "backend" / "data" / "toolkit_docs")).strip(),
        app_version=os.getenv("APP_VERSION", "0.1.0").strip(),
    )


