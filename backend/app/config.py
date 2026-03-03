"""Application configuration — reads from environment variables."""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------- paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
REFERENCES_DIR = STORAGE_DIR / "references"
EXPORTS_DIR = STORAGE_DIR / "exports"
UPLOADS_DIR = STORAGE_DIR / "uploads"
INDEX_PERSIST_PATH = Path(os.getenv("INDEX_PERSIST_PATH", str(STORAGE_DIR / "indices")))

# Legacy global paths (kept for migration reference only)
FAISS_INDEX_PATH = STORAGE_DIR / "faiss.index"
FAISS_MAP_PATH = STORAGE_DIR / "faiss_map.json"

for d in (STORAGE_DIR, REFERENCES_DIR, EXPORTS_DIR, UPLOADS_DIR, INDEX_PERSIST_PATH):
    d.mkdir(parents=True, exist_ok=True)

# ---------- database ----------
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")

# ---------- auth ----------
_DEFAULT_SECRET = "dev-secret-change-me"
JWT_SECRET = os.getenv("JWT_SECRET", _DEFAULT_SECRET)
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))  # 1 hour default
MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))

# Enforce JWT_SECRET in production
if JWT_SECRET == _DEFAULT_SECRET:
    _env = os.getenv("ENV", "development")
    if _env in ("production", "staging"):
        raise RuntimeError(
            "FATAL: JWT_SECRET must be set to a secure random value in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
    logger.warning(
        "Using default JWT_SECRET — this is insecure. Set JWT_SECRET env var for production."
    )

# ---------- OpenAI ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ---------- Sanity / GROQ ----------
SANITY_ENABLED = os.getenv("SANITY_ENABLED", "false").lower() == "true"
SANITY_PROJECT_ID = os.getenv("SANITY_PROJECT_ID", "")
SANITY_TOKEN = os.getenv("SANITY_TOKEN", "")
SANITY_DATASET = os.getenv("SANITY_DATASET", "production")

# ---------- retrieval ----------
RETRIEVAL_THRESHOLD = float(os.getenv("RETRIEVAL_THRESHOLD", "0.20"))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))

# ---------- passage splitting ----------
PASSAGE_TOKEN_SIZE = int(os.getenv("PASSAGE_TOKEN_SIZE", "200"))
PASSAGE_OVERLAP = int(os.getenv("PASSAGE_OVERLAP", "40"))

# ---------- upload limits ----------
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))  # 50 MB

# ---------- CORS ----------
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    if o.strip()
]

# ---------- background jobs ----------
USE_BACKGROUND_JOBS = os.getenv("USE_BACKGROUND_JOBS", "false").lower() == "true"
