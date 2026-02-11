# Q&A From Doctrine

This pipeline generates answers from the local doctrine RAG index (`faiss.index` + `meta.json`). It is extractive and evidence-first. If the retrieved context is not sufficient, the answer is set to `INSUFFICIENT EVIDENCE`.

## Questions input
- Put one question per line in `scripts/questions.txt`.
- The default input path is `scripts/questions.txt`.

## Run
```bash
python -m scripts.answer_questions --in scripts/questions.txt --out scripts/answers.csv
```

Optional flags:
- `--top-k 8`
- `--min-score 0.2`

## Insufficient evidence rule
The script returns `INSUFFICIENT EVIDENCE` when:
- no retrieved chunks pass the relevance threshold, or
- fewer than 3 usable evidence sentences can be extracted, or
- no verifiable citation can be formed from the selected chunks.

## Output schema
`scripts/answers.csv` columns:
- `id`
- `question`
- `answer`
- `citations`
- `status`
- `notes`

## Missing index behavior
If the index is missing, the script exits with a clear message and expected files:
- `backend/data/index/faiss.index`
- `backend/data/index/meta.json`

Build the index with:
```bash
python scripts/build_index.py
```
