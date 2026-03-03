"""Tests for passage splitting and retrieval."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.splitter import split_into_passages

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")


class TestPassageSplitting:
    def test_split_company_overview(self):
        path = os.path.join(SAMPLE_DIR, "company_overview.txt")
        if not os.path.exists(path):
            pytest.skip("company_overview.txt not found")

        with open(path, "r") as f:
            text = f.read()

        passages = split_into_passages(text, "company_overview.txt")
        assert len(passages) >= 1
        assert all("text" in p and "page_or_para" in p for p in passages)

    def test_passages_have_token_count(self):
        text = "This is a test. " * 100
        passages = split_into_passages(text, "test.txt", token_size=50, overlap=10)
        assert len(passages) >= 1
        assert all(p["token_count"] > 0 for p in passages)

    def test_small_text_single_passage(self):
        text = "Short text here."
        passages = split_into_passages(text, "small.txt")
        assert len(passages) == 1
        assert passages[0]["text"] == "Short text here."


class TestEmbeddingsAndRetrieval:
    """Integration test — requires sentence-transformers or OpenAI key."""

    def test_build_and_search(self):
        """Build a tiny index and search it."""
        try:
            import faiss  # noqa: F401
            from app.services.embeddings import build_faiss_index, search
        except (ImportError, ModuleNotFoundError):
            pytest.skip("FAISS or sentence-transformers not installed")

        passages = [
            {
                "passage_id": "p1",
                "reference_id": "r1",
                "text": "NovaTech Solutions achieved ISO 27001 certification in September 2023.",
                "page_or_para": "paragraph 1",
                "filename": "security_policy.txt",
            },
            {
                "passage_id": "p2",
                "reference_id": "r1",
                "text": "The company reported annual revenue of $78.4 million for fiscal year 2025.",
                "page_or_para": "paragraph 2",
                "filename": "company_overview.txt",
            },
        ]

        num = build_faiss_index(passages, user_id="test_user_retrieval")
        assert num == 2

        results = search("Does the company have ISO 27001?", user_id="test_user_retrieval", top_k=2)
        assert len(results) >= 1
        # Top result should be about ISO
        assert "ISO" in results[0]["text"] or "27001" in results[0]["text"]
