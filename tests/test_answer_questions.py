from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.answer_questions import AnswerRow, _build_row_from_evidence, _write_csv


class AnswerQuestionsTests(unittest.TestCase):
    def test_csv_schema_produced(self) -> None:
        rows = [
            AnswerRow(
                qid=1,
                question="Q1",
                answer="A1",
                citations=["C1"],
                status="OK",
                notes="n1",
            )
        ]
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "answers.csv"
            _write_csv(out, rows)
            with out.open("r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                header = next(reader)
        self.assertEqual(header, ["id", "question", "answer", "citations", "status", "notes"])

    def test_insufficient_when_no_chunks(self) -> None:
        row = _build_row_from_evidence(1, "What policy governs X?", [])
        self.assertEqual(row.status, "INSUFFICIENT_EVIDENCE")
        self.assertEqual(row.answer, "INSUFFICIENT EVIDENCE")
        self.assertEqual(row.citations, [])


if __name__ == "__main__":
    unittest.main()
