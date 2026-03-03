"""Embeddings service – OpenAI or sentence-transformers fallback, per-user FAISS index."""

import json
import logging
import os
import threading
import numpy as np
from pathlib import Path
from typing import Optional

from app.config import OPENAI_API_KEY, INDEX_PERSIST_PATH

logger = logging.getLogger(__name__)

# Embedder singleton (shared across users — embedding model is stateless)
_embedder = None
_embedding_dim: int = 384  # default for MiniLM
_embedder_lock = threading.Lock()


def _get_embedder():
    """Return embedding function; prefers OpenAI, falls back to sentence-transformers."""
    global _embedder, _embedding_dim

    if _embedder is not None:
        return _embedder

    with _embedder_lock:
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


# ---------- per-user index paths ----------

def _user_index_dir(user_id: str) -> Path:
    """Return the directory for a specific user's FAISS index."""
    d = INDEX_PERSIST_PATH / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _user_index_path(user_id: str) -> tuple[Path, Path]:
    """Return (faiss_index_path, passage_map_path) for a user."""
    d = _user_index_dir(user_id)
    return d / "faiss.index", d / "faiss_map.json"


def _user_lock_path(user_id: str) -> Path:
    """Return the lock file path for a user's index."""
    return _user_index_dir(user_id) / ".lock"


class _SimpleFileLock:
    """A simple cross-platform file lock using a lock directory."""

    def __init__(self, lock_path: Path, timeout: float = 30.0):
        self.lock_dir = lock_path.with_suffix(".lockdir")
        self.timeout = timeout

    def __enter__(self):
        import time
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self.lock_dir.mkdir(exist_ok=False)
                return self
            except FileExistsError:
                if time.monotonic() > deadline:
                    # Stale lock — force acquire
                    try:
                        self.lock_dir.rmdir()
                    except Exception:
                        pass
                    self.lock_dir.mkdir(exist_ok=True)
                    return self
                time.sleep(0.1)

    def __exit__(self, *args):
        try:
            self.lock_dir.rmdir()
        except Exception:
            pass


def build_faiss_index(passages_with_meta: list[dict], user_id: str) -> int:
    """Build (or rebuild) the FAISS index for a specific user.

    Each entry: {passage_id, reference_id, text, page_or_para, filename}
    Returns number of vectors indexed.
    """
    import faiss

    texts = [p["text"] for p in passages_with_meta]
    if not texts:
        return 0

    vectors = embed_texts(texts)
    dim = vectors.shape[1]

    index = faiss.IndexFlatIP(dim)  # inner product (use normalised vecs for cosine)
    faiss.normalize_L2(vectors)
    index.add(vectors)

    idx_path, map_path = _user_index_path(user_id)
    lock_path = _user_lock_path(user_id)

    with _SimpleFileLock(lock_path):
        faiss.write_index(index, str(idx_path))
        with open(map_path, "w") as f:
            json.dump(passages_with_meta, f)

    logger.info("FAISS index built for user %s: %d vectors (dim=%d)", user_id, index.ntotal, dim)
    return index.ntotal


def search(query: str, user_id: str, top_k: int = 5) -> list[dict]:
    """Return top-K passages with similarity scores for a specific user's index."""
    import faiss

    idx_path, map_path = _user_index_path(user_id)
    lock_path = _user_lock_path(user_id)

    if not idx_path.exists() or not map_path.exists():
        return []

    with _SimpleFileLock(lock_path):
        user_index = faiss.read_index(str(idx_path))
        with open(map_path, "r") as f:
            passage_map = json.load(f)

    if user_index.ntotal == 0:
        return []

    q_vec = embed_texts([query])
    faiss.normalize_L2(q_vec)
    scores, indices = user_index.search(q_vec, min(top_k, user_index.ntotal))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(passage_map):
            continue
        entry = passage_map[idx].copy()
        entry["similarity"] = float(score)
        results.append(entry)
    return results
