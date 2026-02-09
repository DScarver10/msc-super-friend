from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "frontend" / "docs"
TARGET_DIR = ROOT / "web" / "public" / "docs"


def main() -> None:
    if not SOURCE_DIR.exists() or not SOURCE_DIR.is_dir():
        print(f"Warning: source directory not found, skipping copy: {SOURCE_DIR}")
        return

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    copied = 0
    for path in SOURCE_DIR.iterdir():
        if path.is_file():
            shutil.copy2(path, TARGET_DIR / path.name)
            copied += 1

    print(f"Copied {copied} file(s) from {SOURCE_DIR} to {TARGET_DIR}")


if __name__ == "__main__":
    main()
