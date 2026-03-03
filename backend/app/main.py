"""FastAPI application entry-point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import auth, uploads, index, generate, answers, export, references

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Structured Questionnaire Answering Tool",
    version="0.1.0",
    description="Upload questionnaires & references, generate grounded answers with citations.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- routers ----
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])
app.include_router(index.router, prefix="/api/index", tags=["index"])
app.include_router(generate.router, prefix="/api", tags=["generate"])
app.include_router(answers.router, prefix="/api/answers", tags=["answers"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(references.router, prefix="/api/references", tags=["references"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Questionnaire Answering Tool API"}
