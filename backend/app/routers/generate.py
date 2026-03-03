"""Generation router – generate answers for questionnaire questions."""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.routers.auth import get_current_user
from app.models.models import Questionnaire, Question, Run, Answer
from app.services.generation import generate_answer

router = APIRouter()


class GenerateRequest(BaseModel):
    questionnaire_id: str


@router.post("/generate")
def generate_answers(
    body: GenerateRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate answers for every question in a questionnaire."""
    q = db.query(Questionnaire).filter(
        Questionnaire.id == body.questionnaire_id,
        Questionnaire.user_id == user["id"],
    ).first()
    if not q:
        raise HTTPException(404, "Questionnaire not found")

    questions = sorted(q.questions, key=lambda x: x.index)
    if not questions:
        raise HTTPException(400, "No questions parsed from this questionnaire")

    # Create a run
    run = Run(user_id=user["id"], questionnaire_id=q.id)
    db.add(run)
    db.flush()

    results = []
    for question in questions:
        gen = generate_answer(question.text)
        ans = Answer(
            run_id=run.id,
            question_id=question.id,
            answer_text=gen["answer_text"],
            citations=json.dumps(gen["citations"]),
            evidence_snippets=json.dumps(gen["evidence_snippets"]),
            confidence_score=gen["confidence_score"],
        )
        db.add(ans)
        db.flush()
        results.append(
            {
                "answer_id": ans.id,
                "question_id": question.id,
                "question_index": question.index,
                "question_text": question.text,
                "answer_text": gen["answer_text"],
                "citations": gen["citations"],
                "evidence_snippets": gen["evidence_snippets"],
                "confidence_score": gen["confidence_score"],
            }
        )

    db.commit()

    return {
        "run_id": run.id,
        "questionnaire_id": q.id,
        "num_answers": len(results),
        "answers": results,
    }


@router.post("/regenerate/{question_id}")
def regenerate_single(
    question_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Regenerate the answer for a single question (uses latest run)."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(404, "Question not found")

    # Find the latest answer for this question
    existing = (
        db.query(Answer)
        .filter(Answer.question_id == question_id)
        .order_by(Answer.created_at.desc())
        .first()
    )
    if not existing:
        raise HTTPException(404, "No existing answer to regenerate")

    gen = generate_answer(question.text)

    existing.answer_text = gen["answer_text"]
    existing.citations = json.dumps(gen["citations"])
    existing.evidence_snippets = json.dumps(gen["evidence_snippets"])
    existing.confidence_score = gen["confidence_score"]
    existing.is_edited = False

    db.commit()
    db.refresh(existing)

    return {
        "answer_id": existing.id,
        "question_id": question.id,
        "answer_text": gen["answer_text"],
        "citations": gen["citations"],
        "evidence_snippets": gen["evidence_snippets"],
        "confidence_score": gen["confidence_score"],
    }


@router.get("/runs")
def list_runs(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    runs = db.query(Run).filter(Run.user_id == user["id"]).order_by(Run.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "questionnaire_id": r.questionnaire_id,
            "created_at": str(r.created_at),
            "num_answers": len(r.answers),
        }
        for r in runs
    ]


@router.get("/runs/{run_id}")
def get_run(
    run_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = db.query(Run).filter(Run.id == run_id, Run.user_id == user["id"]).first()
    if not run:
        raise HTTPException(404, "Run not found")

    answers = sorted(run.answers, key=lambda a: a.question.index)
    return {
        "id": run.id,
        "questionnaire_id": run.questionnaire_id,
        "created_at": str(run.created_at),
        "answers": [
            {
                "answer_id": a.id,
                "question_id": a.question_id,
                "question_index": a.question.index,
                "question_text": a.question.text,
                "answer_text": a.answer_text,
                "citations": json.loads(a.citations) if a.citations else [],
                "evidence_snippets": json.loads(a.evidence_snippets) if a.evidence_snippets else [],
                "confidence_score": a.confidence_score,
                "is_edited": a.is_edited,
            }
            for a in answers
        ],
    }
