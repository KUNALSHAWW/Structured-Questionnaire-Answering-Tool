"""Upload routers – questionnaire & reference file uploads + parsing."""

import os
import json
import re
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import get_current_user
from app.models.models import Questionnaire, Question, Reference
from app.config import UPLOADS_DIR, REFERENCES_DIR
from app.services.parser import parse_questionnaire, extract_reference_text

router = APIRouter()


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

    # Save file
    dest = UPLOADS_DIR / file.filename
    content = await file.read()
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
    """Upload a reference document (PDF/TXT/CSV)."""
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pdf", "txt", "csv", "docx"):
        raise HTTPException(400, "Unsupported file type. Use PDF, TXT, CSV, or DOCX.")

    dest = REFERENCES_DIR / file.filename
    content = await file.read()
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
