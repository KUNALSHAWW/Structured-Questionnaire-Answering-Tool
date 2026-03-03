"""Tests for questionnaire and reference parsing."""

import os
import sys
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.parser import (
    parse_questionnaire,
    extract_reference_text,
    _looks_like_question,
    _clean_question,
)

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")


class TestQuestionDetection:
    def test_question_mark(self):
        assert _looks_like_question("What is the company revenue?")

    def test_numbered_question(self):
        assert _looks_like_question("1. What is the company mission statement?")

    def test_short_text_rejected(self):
        assert not _looks_like_question("Hello?")

    def test_plain_sentence_rejected(self):
        assert not _looks_like_question("NovaTech Solutions is a technology company.")


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
