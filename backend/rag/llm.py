from __future__ import annotations

from typing import List

from openai import OpenAI

from .retrieve import Evidence


def _build_context_block(evidence: List[Evidence], max_chars_per_chunk: int = 1200) -> str:
    blocks = []
    for i, e in enumerate(evidence, start=1):
        raw_text = getattr(e, "text", None) or getattr(e, "excerpt", "")
        excerpt = raw_text.strip().replace("\r", "\n")
        excerpt = excerpt[:max_chars_per_chunk]
        source = getattr(e, "source", None) or getattr(e, "source_id", None) or getattr(e, "source_type", "unknown")
        blocks.append(
            f"[E{i}] SOURCE={source}\nTITLE={e.title}\nURL={e.url}\nEXCERPT:\n{excerpt}\n"
        )
    return "\n".join(blocks)


def generate_grounded_answer(
    api_key: str,
    model: str,
    question: str,
    evidence: List[Evidence],
) -> str:
    """
    Strictly grounded: the model must use only the evidence excerpts.
    If evidence is insufficient, it should say so plainly.
    """
    client = OpenAI(api_key=api_key)

    system = (
        "You are MSC Super Companion, an evidence-based assistant for Air Force Medical Service Corps officers.\n"
        "You MUST follow these rules:\n"
        "1) Use ONLY the provided evidence excerpts. Do not use outside knowledge.\n"
        "2) If the evidence is insufficient or conflicting, say: 'Insufficient evidence in the indexed sources.'\n"
        "3) Be concise, professional, and policy-style. No jokes, no speculation.\n"
        "4) When you make a claim, reference the evidence IDs like [E1], [E2].\n"
        "5) Do not invent citations.\n"
    )

    context = _build_context_block(evidence)

    user = (
        f"QUESTION:\n{question}\n\n"
        f"EVIDENCE EXCERPTS:\n{context}\n\n"
        "TASK:\n"
        "Answer the question using only the evidence. Include evidence IDs in-line like [E1]."
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()
