# Script to build the AFI 41 doctrine JSON file from a seed CSV.
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED_CSV = ROOT / "web" / "public" / "data" / "afi41_seed.csv"
OUTPUT_JSON = ROOT / "frontend" / "content" / "doctrine_afi41.json"

print(">>> GENERATOR STARTED")
print(">>> CSV PATH:", SEED_CSV.resolve())
print(">>> OUTPUT PATH:", OUTPUT_JSON.resolve())


def main() -> None:
    if not SEED_CSV.exists():
        raise FileNotFoundError(f"CSV not found: {SEED_CSV}")

    doctrine = []

    with SEED_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        print(">>> CSV HEADERS:", reader.fieldnames)

        for row in reader:
            pdf_url = (row.get("official_publication_pdf") or "").strip()

            doctrine.append(
                {
                    "pub": row.get("pub"),
                    "title": row.get("title"),
                    "msc_functional_area": row.get("msc_functional_area"),
                    "official_links": (
                        [
                            {
                                "label": "Official Publication (e-Publishing)",
                                "url": pdf_url,
                            }
                        ]
                        if pdf_url
                        else []
                    ),
                }
            )

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(doctrine, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f">>> WROTE {len(doctrine)} RECORDS")
    print(">>> FIRST RECORD:", doctrine[0])


if __name__ == "__main__":
    main()
