"""Tests for questionnaire and reference parsing."""

import os
import sys
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.parser import (
    parse_questionnaire,
    extract_reference_text,
    _starts_new_question,
    _looks_like_question_fallback,
    _clean_question,
)

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")


class TestQuestionDetection:
    def test_numbered_question(self):
        assert _starts_new_question("1. What is the company mission statement?")

    def test_Q_prefix_question(self):
        assert _starts_new_question("Q3: Describe the DR plan.")

    def test_plain_sentence_not_new_question(self):
        assert not _starts_new_question("NovaTech Solutions is a technology company.")

    def test_fallback_question_mark(self):
        assert _looks_like_question_fallback("What is the company revenue for the year?")

    def test_fallback_short_text_rejected(self):
        assert not _looks_like_question_fallback("Hello?")


class TestCleanQuestion:
    def test_removes_numbering(self):
        assert _clean_question("1. What is revenue?") == "What is revenue?"

    def test_removes_Q_prefix(self):
        assert _clean_question("Q3: Describe the DR plan.") == "Describe the DR plan."

    def test_no_numbering(self):
        assert _clean_question("What is revenue?") == "What is revenue?"


class TestQuestionnaireParsing:
    def test_parse_txt_questionnaire(self):
        path = os.path.join(SAMPLE_DIR, "questionnaire.txt")
        if not os.path.exists(path):
            pytest.skip("Sample questionnaire.txt not found")
        qs = parse_questionnaire(path, "txt")
        assert len(qs) == 10, f"Expected 10 questions, got {len(qs)}"
        assert all("text" in q for q in qs)

    def test_parse_pdf_questionnaire(self):
        path = os.path.join(SAMPLE_DIR, "questionnaire_vendor_assessment.pdf")
        if not os.path.exists(path):
            pytest.skip("Sample PDF questionnaire not found")
        qs = parse_questionnaire(path, "pdf")
        assert len(qs) == 10, f"Expected 10 questions from PDF, got {len(qs)}"
        assert all("text" in q for q in qs)
        # Verify multi-line questions are properly merged
        q2 = qs[1]["text"]
        assert "disaster recovery capabilities" in q2, "Q2 should include continuation text"

    def test_questions_have_location_meta(self):
        path = os.path.join(SAMPLE_DIR, "questionnaire.txt")
        if not os.path.exists(path):
            pytest.skip("Sample questionnaire.txt not found")
        qs = parse_questionnaire(path, "txt")
        assert all("location_meta" in q and q["location_meta"] for q in qs)


class TestReferenceExtraction:
    def test_extract_txt(self):
        path = os.path.join(SAMPLE_DIR, "company_overview.txt")
        if not os.path.exists(path):
            pytest.skip("company_overview.txt not found")
        text = extract_reference_text(path, "txt")
        assert len(text) > 100
        assert "NovaTech" in text

    def test_extract_security_policy(self):
        path = os.path.join(SAMPLE_DIR, "security_policy.txt")
        if not os.path.exists(path):
            pytest.skip("security_policy.txt not found")
        text = extract_reference_text(path, "txt")
        assert "ISO 27001" in text
