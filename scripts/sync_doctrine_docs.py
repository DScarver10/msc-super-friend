from __future__ import annotations

import csv
import shutil
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SEED_CSV = ROOT / "web" / "public" / "data" / "afi41_seed.csv"
FRONTEND_DOCS = ROOT / "frontend" / "docs"
BACKEND_DOCS = ROOT / "backend" / "data" / "toolkit_docs"
WEB_PUBLIC_DOCS = ROOT / "web" / "public" / "docs"


def _safe_name(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name.strip()
    if not name:
        return ""
    return name


def _download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(
            url=url,
            headers={"User-Agent": "msc-super-friend-doc-sync/1.0"},
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
        dest.write_bytes(data)
        return True
    except Exception:
        return False


def main() -> None:
    if not SEED_CSV.exists():
        raise FileNotFoundError(f"Missing CSV: {SEED_CSV}")

    FRONTEND_DOCS.mkdir(parents=True, exist_ok=True)
    BACKEND_DOCS.mkdir(parents=True, exist_ok=True)
    WEB_PUBLIC_DOCS.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    skipped = 0
    failed = 0

    with SEED_CSV.open("r", encoding="utf-8", newline="") as f:
        rows = csv.DictReader(f)
        for row in rows:
            url = (row.get("official_publication_pdf") or "").strip()
            if not url.lower().startswith("http"):
                skipped += 1
                continue

            name = _safe_name(url)
            if not name.lower().endswith(".pdf"):
                skipped += 1
                continue

            frontend_target = FRONTEND_DOCS / name
            if not frontend_target.exists():
                ok = _download(url, frontend_target)
                if not ok:
                    failed += 1
                    continue
                downloaded += 1
            else:
                skipped += 1

            shutil.copy2(frontend_target, BACKEND_DOCS / name)
            shutil.copy2(frontend_target, WEB_PUBLIC_DOCS / name)

    print(
        f"Doctrine doc sync complete. downloaded={downloaded} skipped={skipped} failed={failed} "
        f"frontend={FRONTEND_DOCS} backend={BACKEND_DOCS} web={WEB_PUBLIC_DOCS}"
    )


if __name__ == "__main__":
    main()
