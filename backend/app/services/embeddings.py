"""Embeddings service – OpenAI or sentence-transformers fallback, FAISS index."""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Optional

from app.config import OPENAI_API_KEY, FAISS_INDEX_PATH, FAISS_MAP_PATH

logger = logging.getLogger(__name__)

# Global state
_faiss_index = None
_passage_map: list[dict] = []  # [{passage_id, reference_id, text, page_or_para, filename}]
_embedder = None
_embedding_dim: int = 384  # default for MiniLM


def _get_embedder():
    """Return embedding function; prefers OpenAI, falls back to sentence-transformers."""
    global _embedder, _embedding_dim

    if _embedder is not None:
        return _embedder

    if OPENAI_API_KEY:
        logger.info("Using OpenAI embeddings (text-embedding-3-small)")
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)

        def _openai_embed(texts: list[str]) -> np.ndarray:
            resp = client.embeddings.create(
                input=texts, model="text-embedding-3-small"
            )
            vecs = [d.embedding for d in resp.data]
            return np.array(vecs, dtype="float32")

        _embedder = _openai_embed
        _embedding_dim = 1536
    else:
        logger.info("Using sentence-transformers (all-MiniLM-L6-v2)")
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        _embedding_dim = model.get_sentence_embedding_dimension()

        def _st_embed(texts: list[str]) -> np.ndarray:
            return model.encode(texts, normalize_embeddings=True).astype("float32")

        _embedder = _st_embed

    return _embedder


def embed_texts(texts: list[str]) -> np.ndarray:
    embedder = _get_embedder()
    return embedder(texts)


def build_faiss_index(passages_with_meta: list[dict]) -> int:
    """Build (or rebuild) the FAISS index from passages.

    Each entry: {passage_id, reference_id, text, page_or_para, filename}
    Returns number of vectors indexed.
    """
    import faiss

    global _faiss_index, _passage_map

    texts = [p["text"] for p in passages_with_meta]
    if not texts:
        return 0

    vectors = embed_texts(texts)
    dim = vectors.shape[1]

    index = faiss.IndexFlatIP(dim)  # inner product (use normalised vecs for cosine)
    # Normalise vectors for cosine similarity
    faiss.normalize_L2(vectors)
    index.add(vectors)

    _faiss_index = index
    _passage_map = passages_with_meta

    # Persist
    faiss.write_index(index, str(FAISS_INDEX_PATH))
    with open(FAISS_MAP_PATH, "w") as f:
        json.dump(_passage_map, f)

    logger.info("FAISS index built with %d vectors (dim=%d)", index.ntotal, dim)
    return index.ntotal


def load_faiss_index():
    """Load persisted FAISS index + passage map if available."""
    import faiss

    global _faiss_index, _passage_map
    if FAISS_INDEX_PATH.exists() and FAISS_MAP_PATH.exists():
        _faiss_index = faiss.read_index(str(FAISS_INDEX_PATH))
        with open(FAISS_MAP_PATH, "r") as f:
            _passage_map = json.load(f)
        logger.info("Loaded FAISS index with %d vectors", _faiss_index.ntotal)


def search(query: str, top_k: int = 5) -> list[dict]:
    """Return top-K passages with similarity scores."""
    import faiss

    global _faiss_index, _passage_map

    if _faiss_index is None:
        load_faiss_index()

    if _faiss_index is None or _faiss_index.ntotal == 0:
        return []

    q_vec = embed_texts([query])
    faiss.normalize_L2(q_vec)
    scores, indices = _faiss_index.search(q_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        entry = _passage_map[idx].copy()
        entry["similarity"] = float(score)
        results.append(entry)
    return results
