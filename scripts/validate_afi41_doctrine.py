from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "frontend" / "content" / "doctrine_afi41.json"

BAD_WORDS = ["PLACEHOLDER", "TODO", "PASTE"]


def main() -> None:
    if not JSON_PATH.exists():
        print(f"Missing: {JSON_PATH}")
        sys.exit(1)

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    issues = 0

    for i, item in enumerate(data, start=1):
        text_fields = [
            item.get("pub", ""),
            item.get("title", ""),
            item.get("why_it_matters", ""),
            " ".join(item.get("use_cases", []) or []),
            item.get("notes", ""),
        ]
        joined = " ".join(text_fields)
        if any(b in joined for b in BAD_WORDS):
            issues += 1
            print(f"[WARN] Entry {i} has placeholder text: {item.get('pub')} — {item.get('title')}")

        links = item.get("official_links", []) or []
        if not links:
            print(f"[INFO] Entry {i} missing official link: {item.get('pub')} — {item.get('title')}")

    print(f"\nValidation complete. Entries: {len(data)} • Placeholder issues: {issues}")
    # Exit non-zero if placeholders exist (useful later in CI)
    if issues:
        sys.exit(2)


if __name__ == "__main__":
    main()
