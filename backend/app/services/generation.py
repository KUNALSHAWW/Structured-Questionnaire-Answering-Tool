"""LLM generation service – grounded answer generation with citations."""

import json
import logging
import re
from collections import Counter
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

    # Improved confidence scoring: map similarity to a more meaningful 0-100 range
    # Cosine similarity with MiniLM typically ranges 0.15-0.80 for relevant text
    # Map: <0.20 → 0-20, 0.20-0.40 → 20-60, 0.40-0.60 → 60-85, >0.60 → 85-100
    if max_sim < 0.20:
        confidence_score = int(max_sim * 100)
    elif max_sim < 0.40:
        confidence_score = int(20 + (max_sim - 0.20) * 200)  # 20-60
    elif max_sim < 0.60:
        confidence_score = int(60 + (max_sim - 0.40) * 125)  # 60-85
    else:
        confidence_score = int(min(85 + (max_sim - 0.60) * 75, 100))  # 85-100

    if max_sim < threshold:
        return _not_found_result(confidence_score=confidence_score)

    # Build passages block
    passages_block = _build_passages_block(results)

    # Call LLM
    raw_reply = _call_llm(question_text, passages_block, results)

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


def _call_llm(question: str, passages_block: str, results: list[dict] | None = None) -> str:
    """Call an LLM (OpenAI preferred, else smart extractive fallback)."""
    user_msg = f"QUESTION:\n{question}\n\nPASSAGES (top K retrieved — label each as [file | page/para] before the passage):\n{passages_block}"

    if OPENAI_API_KEY:
        return _call_openai(user_msg)
    else:
        return _extractive_fallback(question, results or [])


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


def _extractive_fallback(question: str, results: list[dict]) -> str:
    """When no LLM API key is available, produce a smart extractive answer
    by selecting the most relevant sentences from top passages."""
    if not results:
        return "Not found in references."

    question_lower = question.lower()
    # Extract meaningful keywords from the question (skip stop words)
    stop_words = {
        "what", "is", "the", "a", "an", "of", "in", "for", "to", "and", "or",
        "how", "does", "do", "are", "was", "were", "has", "have", "had", "be",
        "been", "being", "can", "could", "would", "should", "will", "shall",
        "may", "might", "this", "that", "these", "those", "it", "its", "they",
        "their", "them", "we", "our", "you", "your", "he", "she", "his", "her",
        "which", "who", "whom", "whose", "when", "where", "why", "with", "from",
        "by", "on", "at", "about", "into", "through", "during", "before",
        "after", "above", "below", "between", "s", "t", "describe", "explain",
        "provide", "details", "company", "organization", "mention", "mentioned",
    }
    keywords = [
        w for w in re.findall(r"\b[a-z]+\b", question_lower)
        if w not in stop_words and len(w) > 2
    ]

    # Also extract numbers and proper-noun-like tokens from original question
    numbers = re.findall(r"\b\d+\b", question)
    proper_tokens = re.findall(r"\b[A-Z][a-z]+\b", question)
    keywords.extend([n for n in numbers])
    keywords.extend([p.lower() for p in proper_tokens])

    # Collect and score sentences from top passages
    scored_sentences: list[tuple[float, str, str, str]] = []  # (score, sentence, citation, filename)

    for r in results[:3]:  # Use top 3 passages
        text = _clean_passage_text(r["text"])
        citation = f"{r['filename']} | {r['page_or_para']}"

        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)

        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 15:  # Skip tiny fragments
                continue
            # Skip lines that look like document titles / headers
            if _is_header_line(sent):
                continue

            # Score sentence by keyword overlap
            sent_lower = sent.lower()
            score = 0.0
            for kw in keywords:
                if kw in sent_lower:
                    score += 1.0
            # Boost sentences with numbers (often contain factual data)
            if re.search(r"\d", sent):
                score += 0.5
            # Boost based on passage relevance (similarity rank)
            score += r["similarity"] * 2

            scored_sentences.append((score, sent, citation, r["filename"]))

    if not scored_sentences:
        # Fallback: just use cleaned top passage text
        top_text = _clean_passage_text(results[0]["text"])
        citation = f"{results[0]['filename']} | {results[0]['page_or_para']}"
        return (
            f"Answer:\n{top_text[:500]}\n"
            f"CITATIONS: [{citation}]\n"
            f"EVIDENCE_SNIPPETS:\n- [{citation}] \"{top_text[:200]}\""
        )

    # Sort by score descending, take top sentences
    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    # Select top 3-5 sentences, deduplicating
    seen = set()
    selected = []
    citations_used = set()
    for score, sent, citation, filename in scored_sentences:
        # Simple dedup by first 40 chars
        key = sent[:40].lower()
        if key in seen:
            continue
        seen.add(key)
        selected.append((sent, citation))
        citations_used.add(citation)
        if len(selected) >= 5:
            break

    answer_text = " ".join(_clean_sentence(s[0]) for s in selected)
    citations_list = list(citations_used)

    # Build evidence snippets from selected sentences
    evidence_lines = []
    for sent, citation in selected[:3]:
        evidence_lines.append(f"- [{citation}] \"{sent[:200]}\"")

    return (
        f"Answer:\n{answer_text}\n"
        f"CITATIONS: {', '.join(f'[{c}]' for c in citations_list)}\n"
        f"EVIDENCE_SNIPPETS:\n" + "\n".join(evidence_lines)
    )


def _clean_passage_text(text: str) -> str:
    """Remove document titles, headers, and noise from passage text."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if _is_header_line(line):
            continue
        cleaned.append(line)
    return " ".join(cleaned)


def _is_header_line(line: str) -> bool:
    """Detect lines that are document titles or section headers to skip."""
    line = line.strip()
    if not line:
        return True
    # Skip lines that look like "CompanyName – Report Title 2025"
    if re.search(r"[–—-]\s*(HR|People|Finance|Revenue|Marketing|Sales|Report|Summary|Review|Plan|Strategy|Data|Privacy|Security|Policy|Company|Overview|ESG|Sustainability|Disaster|Recovery|Business|Continuity)", line, re.IGNORECASE):
        return True
    # Skip lines with "Document Version X.X" or "Document ID:"
    if re.search(r"Document\s+(Version|ID)\s*[:\d]", line, re.IGNORECASE):
        return True
    # Skip "Effective Date:" lines
    if re.search(r"Effective\s+Date\s*:", line, re.IGNORECASE):
        return True
    # Skip "Last Updated:" lines
    if re.search(r"Last\s+Updated\s*:", line, re.IGNORECASE):
        return True
    # Skip short all-caps or title-case lines that look like headings (≤8 words)
    if len(line.split()) <= 8 and (line.isupper() or line.istitle()):
        return True
    # Skip standalone date-like headers
    if re.match(r"^(Q[1-4]\s+\d{4}|FY\s*\d{4}|Year\s+\d{4}|January|February|March|April|May|June|July|August|September|October|November|December)\s*\d*$", line, re.IGNORECASE):
        return True
    return False


def _clean_sentence(sentence: str) -> str:
    """Remove leading document titles/metadata from a sentence."""
    # Only strip patterns with em-dash/en-dash (not regular hyphens): "CompanyName – Title YYYY"
    cleaned = re.sub(
        r"^[A-Z][A-Za-z\s]{2,40}[–—]\s*[A-Za-z&\s]+(?:\d{4})?\s*",
        "",
        sentence,
    ).strip()
    # If we stripped too much, keep original
    if len(cleaned) < 15:
        return sentence.strip()
    return cleaned


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
