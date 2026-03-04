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

    def test_pdf_page_and_section_splitting(self):
        """PDF text with form-feeds and numbered sections produces granular passages."""
        text = (
            "1. Infrastructure Overview\nNovaTech operates a hybrid cloud. "
            "The primary data center is in Austin, Texas.\n"
            "2. Cybersecurity\nNovaTech holds ISO 27001 and SOC 2 Type II certs. "
            "Annual pen testing by CrowdStrike.\n"
            "3. Backup\nDatabases are backed up every 4 hours using AWS Backup."
            "\f"
            "4. Disaster Recovery\nThe BCP was updated in September 2025. "
            "DR failover tests are conducted bi-annually."
        )
        passages = split_into_passages(text, "test_report.pdf")
        # Should have at least 4 passages (3 sections on page 1 + page 2)
        assert len(passages) >= 4
        # Check labels contain page and section info
        labels = [p["page_or_para"] for p in passages]
        assert any("page 1" in l and "section" in l for l in labels)
        assert any("page 2" in l for l in labels)
        # No "paragraph 1" — everything should be page/section based
        assert not any(l == "paragraph 1" for l in labels)

    def test_section_header_splitting_no_pages(self):
        """Text with section headers but no form-feeds uses section-based split."""
        text = (
            "1. Revenue\nTotal revenue was $78M in FY2025.\n"
            "2. Profitability\nGross margin was 71%. Operating income was $12M.\n"
            "3. Audit\nFinancials were audited by KPMG under GAAP.\n"
        )
        passages = split_into_passages(text, "financials.txt")
        assert len(passages) == 3
        labels = [p["page_or_para"] for p in passages]
        assert labels == ["section 1", "section 2", "section 3"]


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
