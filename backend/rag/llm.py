from __future__ import annotations

from typing import List

from openai import OpenAI

from .retrieve import Evidence


def _build_context_block(evidence: List[Evidence], max_chars_per_chunk: int = 1200) -> str:
    blocks = []
    for i, e in enumerate(evidence, start=1):
        excerpt = (e.excerpt or "").strip().replace("\r", "\n")[:max_chars_per_chunk]
        section = e.section or "n/a"
        subsection = e.subsection or "n/a"
        page = str(e.page) if e.page is not None else "n/a"
        blocks.append(
            f"[E{i}] SOURCE={e.source_id}\n"
            f"TITLE={e.title}\n"
            f"PUB={e.pub or 'n/a'}\n"
            f"SECTION={section}\n"
            f"SUBSECTION={subsection}\n"
            f"PAGE={page}\n"
            f"URL={e.url or e.local_path or 'n/a'}\n"
            f"EXCERPT:\n{excerpt}\n"
        )
    return "\n".join(blocks)


def generate_grounded_answer(
    api_key: str,
    model: str,
    question: str,
    evidence: List[Evidence],
) -> str:
    if not evidence:
        return "Insufficient evidence in the indexed sources."

    client = OpenAI(api_key=api_key)
    context = _build_context_block(evidence)

    system = (
        "You are MSC Super Companion. Answer ONLY from provided evidence.\n"
        "Do not use outside knowledge. Do not speculate. Do not infer unsupported facts.\n"
        "If evidence is insufficient, output exactly: Insufficient evidence in the indexed sources.\n"
        "Output format must be exactly:\n"
        "Answer: <3-8 concise sentences with [E#] markers>\n"
        "Evidence: <1-3 bullet points, each with [E#]>\n"
        "Limitations: <one short sentence about uncertainty or 'None.'>\n"
    )

    user = (
        f"QUESTION:\n{question}\n\n"
        f"EVIDENCE:\n{context}\n\n"
        "Return only the required template."
    )

    resp = client.chat.completions.create(
        model=model,
        temperature=0.0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = (resp.choices[0].message.content or "").strip()
    if not content:
        return "Insufficient evidence in the indexed sources."
    return content
