"""Application configuration — reads from environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------- paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
REFERENCES_DIR = STORAGE_DIR / "references"
EXPORTS_DIR = STORAGE_DIR / "exports"
UPLOADS_DIR = STORAGE_DIR / "uploads"
FAISS_INDEX_PATH = STORAGE_DIR / "faiss.index"
FAISS_MAP_PATH = STORAGE_DIR / "faiss_map.json"

for d in (STORAGE_DIR, REFERENCES_DIR, EXPORTS_DIR, UPLOADS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ---------- database ----------
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")

# ---------- auth ----------
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "1440"))  # 24 h

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
