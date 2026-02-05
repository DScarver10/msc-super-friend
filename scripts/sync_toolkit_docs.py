import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DOCS = ROOT / "frontend" / "docs"
BACKEND_DOCS = ROOT / "backend" / "data" / "toolkit_docs"


def main() -> None:
    if not FRONTEND_DOCS.exists():
        raise FileNotFoundError(f"Missing: {FRONTEND_DOCS}")

    BACKEND_DOCS.mkdir(parents=True, exist_ok=True)

    copied = 0
    for p in FRONTEND_DOCS.iterdir():
        if p.is_file():
            dest = BACKEND_DOCS / p.name
            shutil.copy2(p, dest)
            copied += 1

    print(f"Synced {copied} file(s) to {BACKEND_DOCS}")


if __name__ == "__main__":
    main()
