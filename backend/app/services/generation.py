"""LLM generation service – grounded answer generation with citations."""

import json
import logging
import re
from typing import Optional

from app.config import OPENAI_API_KEY, RETRIEVAL_THRESHOLD, RETRIEVAL_TOP_K
from app.services.embeddings import search

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a strict answer generator. You must ONLY use the PASSAGES provided below to answer the QUESTION. Do NOT use outside knowledge. If there is no explicit supporting text in the passages, respond exactly with:
Not found in references.

When you answer:
- Keep the answer concise (3–6 sentences).
- After the answer, provide a CITATIONS line listing at least one exact citation in this format: [filename | page N] or [filename | paragraph M].
- After CITATIONS, provide a short Evidence Snippet block that quotes (verbatim) the sentence(s) from the passage used to support the answer.
- If the passages contradict each other, state that evidence is contradictory and cite each source.
- Do not invent numbers, dates, names, or policies not present in the passages.

REPLY FORMAT (machine parseable):
Answer:
<your answer text>
CITATIONS: [filename | page X], ...
EVIDENCE_SNIPPETS:
- [filename | page X] "..." (exact short quote)

If not found, the reply must be exactly:
Not found in references."""


def generate_answer(question_text: str, threshold: float = RETRIEVAL_THRESHOLD, top_k: int = RETRIEVAL_TOP_K) -> dict:
    """Retrieve passages and generate a grounded answer.

    Returns: {answer_text, citations: list[str], evidence_snippets: list[str], confidence_score: int}
    """
    # Retrieve
    results = search(question_text, top_k=top_k)

    if not results:
        return _not_found_result()

    max_sim = max(r["similarity"] for r in results)
    confidence_score = int(min(max_sim * 0.9, 1.0) * 100)

    if max_sim < threshold:
        return _not_found_result(confidence_score=confidence_score)

    # Build passages block
    passages_block = _build_passages_block(results)

    # Call LLM
    raw_reply = _call_llm(question_text, passages_block)

    # Parse reply
    parsed = _parse_reply(raw_reply, results)
    parsed["confidence_score"] = confidence_score
    return parsed


def _not_found_result(confidence_score: int = 0) -> dict:
    return {
        "answer_text": "Not found in references.",
        "citations": [],
        "evidence_snippets": [],
        "confidence_score": confidence_score,
    }


def _build_passages_block(results: list[dict]) -> str:
    lines = []
    for r in results:
        label = f"[{r['filename']} | {r['page_or_para']}]"
        lines.append(f"{label} {r['text'][:800]}")
    return "\n\n".join(lines)


def _call_llm(question: str, passages_block: str) -> str:
    """Call an LLM (OpenAI preferred, else simple extractive fallback)."""
    user_msg = f"QUESTION:\n{question}\n\nPASSAGES (top K retrieved — label each as [file | page/para] before the passage):\n{passages_block}"

    if OPENAI_API_KEY:
        return _call_openai(user_msg)
    else:
        return _extractive_fallback(question, passages_block)


def _call_openai(user_msg: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.1,
        max_tokens=600,
    )
    return resp.choices[0].message.content or ""


def _extractive_fallback(question: str, passages_block: str) -> str:
    """When no LLM API key is available, produce a simple extractive answer
    by selecting the most relevant passage as the answer."""
    # Just use the top passage as the answer
    lines = passages_block.strip().split("\n\n")
    if not lines:
        return "Not found in references."

    top_line = lines[0]
    # Extract citation label
    match = re.match(r"\[(.+?)\]\s*(.*)", top_line, re.DOTALL)
    if match:
        citation = match.group(1)
        text = match.group(2).strip()
    else:
        citation = "unknown"
        text = top_line

    snippet = text[:300]
    answer = text[:500] if len(text) > 10 else "Not found in references."

    return (
        f"Answer:\n{answer}\n"
        f"CITATIONS: [{citation}]\n"
        f"EVIDENCE_SNIPPETS:\n- [{citation}] \"{snippet}\""
    )


def _parse_reply(raw: str, results: list[dict]) -> dict:
    """Parse the LLM reply into structured fields."""
    if raw.strip() == "Not found in references.":
        return _not_found_result()

    answer_text = ""
    citations: list[str] = []
    evidence_snippets: list[str] = []

    # Extract answer
    ans_match = re.search(r"(?:^|\n)Answer:\s*\n?(.*?)(?:\nCITATIONS:|\Z)", raw, re.DOTALL)
    if ans_match:
        answer_text = ans_match.group(1).strip()
    else:
        answer_text = raw.strip()

    # Extract citations
    cit_match = re.search(r"CITATIONS:\s*(.*?)(?:\nEVIDENCE|\Z)", raw, re.DOTALL)
    if cit_match:
        cit_text = cit_match.group(1).strip()
        citations = re.findall(r"\[([^\]]+)\]", cit_text)

    # Extract evidence snippets
    ev_match = re.search(r"EVIDENCE_SNIPPETS:\s*(.*)", raw, re.DOTALL)
    if ev_match:
        ev_text = ev_match.group(1).strip()
        for line in ev_text.split("\n"):
            line = line.strip().lstrip("-").strip()
            if line:
                evidence_snippets.append(line[:300])

    # Fallback citations from retrieved passages
    if not citations and results:
        citations = [f"{r['filename']} | {r['page_or_para']}" for r in results[:2]]

    # Fallback evidence snippets
    if not evidence_snippets and results:
        evidence_snippets = [r["text"][:300] for r in results[:2]]

    return {
        "answer_text": answer_text,
        "citations": citations,
        "evidence_snippets": evidence_snippets,
        "confidence_score": 0,
    }
