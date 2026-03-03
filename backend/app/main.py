"""FastAPI application entry-point."""

import logging
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import engine, Base
from app.config import ALLOWED_ORIGINS
from app.routers import auth, uploads, index, generate, answers, export, references

# ---------- Structured logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("app")

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Structured Questionnaire Answering Tool",
    version="1.0.0",
    description="Upload questionnaires & references, generate grounded answers with citations.",
)

# ---------- CORS – explicit origins ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ---------- Request logging middleware ----------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s %s %.0fms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


# ---------- Global exception handler ----------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "code": 500,
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


# ---- routers ----
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])
app.include_router(index.router, prefix="/api/index", tags=["index"])
app.include_router(generate.router, prefix="/api", tags=["generate"])
app.include_router(answers.router, prefix="/api/answers", tags=["answers"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(references.router, prefix="/api/references", tags=["references"])


# ---------- Health endpoint ----------
@app.get("/api/health", tags=["health"])
def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": app.version,
    }


@app.get("/")
def root():
    return {"status": "ok", "message": "Questionnaire Answering Tool API"}
