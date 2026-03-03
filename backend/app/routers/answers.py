"""Answers router – manual edit endpoint."""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.routers.auth import get_current_user
from app.models.models import Answer

router = APIRouter()


class EditAnswerRequest(BaseModel):
    answer_text: str
    citations: Optional[list[str]] = None


@router.put("/{answer_id}")
def edit_answer(
    answer_id: str,
    body: EditAnswerRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ans = db.query(Answer).filter(Answer.id == answer_id).first()
    if not ans:
        raise HTTPException(404, "Answer not found")

    ans.answer_text = body.answer_text
    if body.citations is not None:
        ans.citations = json.dumps(body.citations)
    ans.is_edited = True
    db.commit()
    db.refresh(ans)

    return {
        "answer_id": ans.id,
        "answer_text": ans.answer_text,
        "citations": json.loads(ans.citations) if ans.citations else [],
        "is_edited": ans.is_edited,
    }
