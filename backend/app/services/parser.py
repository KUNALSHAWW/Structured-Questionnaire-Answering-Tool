"""Parsing utilities for questionnaires and reference documents."""

import re
import csv
import io


def parse_questionnaire(filepath: str, ext: str) -> list[dict]:
    """Parse a questionnaire file into a list of {text, location_meta} dicts."""
    if ext == "pdf":
        return _parse_questionnaire_pdf(filepath)
    elif ext == "xlsx":
        return _parse_questionnaire_xlsx(filepath)
    elif ext == "txt":
        return _parse_questionnaire_txt(filepath)
    return []


def _parse_questionnaire_pdf(filepath: str) -> list[dict]:
    import pdfplumber

    questions = []
    with pdfplumber.open(filepath) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            for line in text.split("\n"):
                line = line.strip()
                if _looks_like_question(line):
                    questions.append(
                        {"text": _clean_question(line), "location_meta": f"page {page_num}"}
                    )
    return questions


def _parse_questionnaire_xlsx(filepath: str) -> list[dict]:
    from openpyxl import load_workbook

    wb = load_workbook(filepath, read_only=True)
    ws = wb.active
    questions = []
    for row_num, row in enumerate(ws.iter_rows(values_only=True), start=1):
        for cell in row:
            if cell and isinstance(cell, str) and _looks_like_question(cell.strip()):
                questions.append(
                    {"text": _clean_question(cell.strip()), "location_meta": f"row {row_num}"}
                )
    wb.close()
    return questions


def _parse_questionnaire_txt(filepath: str) -> list[dict]:
    questions = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if _looks_like_question(line):
                questions.append(
                    {"text": _clean_question(line), "location_meta": f"line {line_num}"}
                )
    return questions


def _looks_like_question(text: str) -> bool:
    """Heuristic: line ends with '?' or starts with a number/bullet followed by text."""
    if not text or len(text) < 8:
        return False
    if text.endswith("?"):
        return True
    # Numbered patterns: "1.", "1)", "Q1.", "Q1:", etc.
    if re.match(r"^(Q?\d+[\.\)\:])\s+.{8,}", text, re.IGNORECASE):
        return True
    return False


def _clean_question(text: str) -> str:
    """Remove leading numbering but keep the question text."""
    cleaned = re.sub(r"^Q?\d+[\.\)\:]\s*", "", text, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else text


# ---- reference text extraction ----

def extract_reference_text(filepath: str, ext: str) -> str:
    if ext == "pdf":
        return _extract_pdf(filepath)
    elif ext == "txt":
        return _extract_txt(filepath)
    elif ext == "csv":
        return _extract_csv(filepath)
    elif ext == "docx":
        return _extract_docx(filepath)
    return ""


def _extract_pdf(filepath: str) -> str:
    import pdfplumber

    texts = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            texts.append(t)
    return "\n".join(texts)


def _extract_txt(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _extract_csv(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        rows = [", ".join(row) for row in reader]
    return "\n".join(rows)


def _extract_docx(filepath: str) -> str:
    from docx import Document

    doc = Document(filepath)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
