"""Upload routers – questionnaire & reference file uploads + parsing."""

import os
import json
import re
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import get_current_user
from app.models.models import Questionnaire, Question, Reference
from app.config import UPLOADS_DIR, REFERENCES_DIR, MAX_UPLOAD_BYTES
from app.services.parser import parse_questionnaire, extract_reference_text

router = APIRouter()

# ---------- upload helpers ----------

def _safe_filename(original: str) -> str:
    """Sanitize filename: strip path components, prefix with UUID."""
    name = Path(original).name  # strip any directory traversal
    name = re.sub(r"[^\w.\-]", "_", name)  # keep only safe chars
    return f"{uuid.uuid4().hex}_{name}"


def _user_upload_dir(user_id: str) -> Path:
    """Return per-user upload directory, creating it if needed."""
    d = UPLOADS_DIR / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _user_reference_dir(user_id: str) -> Path:
    """Return per-user reference directory, creating it if needed."""
    d = REFERENCES_DIR / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d


async def _read_upload(file: UploadFile) -> bytes:
    """Read uploaded file with size limit enforcement."""
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            413,
            f"File too large. Maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )
    return content


@router.post("/questionnaire")
async def upload_questionnaire(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a questionnaire (PDF/XLSX/TXT) and parse into questions."""
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pdf", "xlsx", "txt"):
        raise HTTPException(400, "Unsupported file type. Use PDF, XLSX, or TXT.")

    content = await _read_upload(file)

    # Save with sanitized name in per-user dir
    safe_name = _safe_filename(file.filename)
    dest = _user_upload_dir(user["id"]) / safe_name
    with open(dest, "wb") as f:
        f.write(content)

    # Parse
    questions_raw = parse_questionnaire(str(dest), ext)

    # Persist
    q = Questionnaire(user_id=user["id"], filename=file.filename, file_type=ext)
    db.add(q)
    db.flush()

    question_objects = []
    for idx, qt in enumerate(questions_raw):
        qobj = Question(
            questionnaire_id=q.id,
            index=idx + 1,
            text=qt["text"],
            location_meta=qt.get("location_meta", ""),
        )
        db.add(qobj)
        question_objects.append(qobj)

    db.commit()
    db.refresh(q)

    return {
        "questionnaire_id": q.id,
        "filename": file.filename,
        "num_questions": len(question_objects),
        "questions": [
            {"id": qo.id, "index": qo.index, "text": qo.text}
            for qo in question_objects
        ],
    }


@router.post("/reference")
async def upload_reference(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a reference document (PDF/TXT/CSV/DOCX)."""
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pdf", "txt", "csv", "docx"):
        raise HTTPException(400, "Unsupported file type. Use PDF, TXT, CSV, or DOCX.")

    content = await _read_upload(file)

    # Save with sanitized name in per-user dir
    safe_name = _safe_filename(file.filename)
    dest = _user_reference_dir(user["id"]) / safe_name
    with open(dest, "wb") as f:
        f.write(content)

    # Extract text and store
    extracted_text = extract_reference_text(str(dest), ext)

    ref = Reference(
        user_id=user["id"],
        filename=file.filename,
        file_type=ext,
        stored_path=str(dest),
    )
    db.add(ref)
    db.commit()
    db.refresh(ref)

    return {
        "reference_id": ref.id,
        "filename": file.filename,
        "text_length": len(extracted_text),
    }


@router.get("/questionnaires")
def list_questionnaires(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qs = db.query(Questionnaire).filter(Questionnaire.user_id == user["id"]).all()
    return [
        {
            "id": q.id,
            "filename": q.filename,
            "file_type": q.file_type,
            "created_at": str(q.created_at),
            "num_questions": len(q.questions),
        }
        for q in qs
    ]


@router.get("/questionnaire/{qid}/questions")
def get_questions(
    qid: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Questionnaire).filter(
        Questionnaire.id == qid, Questionnaire.user_id == user["id"]
    ).first()
    if not q:
        raise HTTPException(404, "Questionnaire not found")
    return [
        {"id": qu.id, "index": qu.index, "text": qu.text}
        for qu in sorted(q.questions, key=lambda x: x.index)
    ]


@router.get("/references")
def list_references(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    refs = db.query(Reference).filter(Reference.user_id == user["id"]).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "file_type": r.file_type,
            "created_at": str(r.created_at),
        }
        for r in refs
    ]
