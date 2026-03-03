"""Generation router – generate answers for questionnaire questions."""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.routers.auth import get_current_user
from app.models.models import Questionnaire, Question, Run, Answer, Job
from app.services.generation import generate_answer
from app.auth_utils import verify_question_ownership, verify_answer_ownership
from app.config import USE_BACKGROUND_JOBS

router = APIRouter()


class GenerateRequest(BaseModel):
    questionnaire_id: str


def _run_generation_sync(q, questions, user_id: str, db: Session) -> dict:
    """Execute generation synchronously and return results."""
    run = Run(user_id=user_id, questionnaire_id=q.id)
    db.add(run)
    db.flush()

    results = []
    for question in questions:
        gen = generate_answer(question.text, user_id=user_id)
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


@router.post("/generate")
def generate_answers(
    body: GenerateRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate answers. Uses background jobs if USE_BACKGROUND_JOBS=true."""
    q = db.query(Questionnaire).filter(
        Questionnaire.id == body.questionnaire_id,
        Questionnaire.user_id == user["id"],
    ).first()
    if not q:
        raise HTTPException(404, "Questionnaire not found")

    questions = sorted(q.questions, key=lambda x: x.index)
    if not questions:
        raise HTTPException(400, "No questions parsed from this questionnaire")

    if USE_BACKGROUND_JOBS:
        job = Job(
            user_id=user["id"],
            type="generate",
            payload_json=json.dumps({"questionnaire_id": body.questionnaire_id}),
            status="pending",
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return {
            "job_id": job.id,
            "status": "pending",
            "message": "Generation job queued. Poll GET /api/jobs/{job_id} for status.",
        }

    return _run_generation_sync(q, questions, user["id"], db)


@router.post("/regenerate/{question_id}")
def regenerate_single(
    question_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Regenerate the answer for a single question (uses latest run)."""
    question = verify_question_ownership(question_id, user["id"], db)

    existing = (
        db.query(Answer)
        .join(Run, Answer.run_id == Run.id)
        .filter(Answer.question_id == question_id, Run.user_id == user["id"])
        .order_by(Answer.created_at.desc())
        .first()
    )
    if not existing:
        raise HTTPException(404, "No existing answer to regenerate")

    gen = generate_answer(question.text, user_id=user["id"])

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


# ---------- job polling ----------

@router.get("/jobs/{job_id}")
def get_job(
    job_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Poll job status. Returns status and result when complete."""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user["id"]).first()
    if not job:
        raise HTTPException(404, "Job not found")

    response = {
        "job_id": job.id,
        "type": job.type,
        "status": job.status,
        "created_at": str(job.created_at),
        "updated_at": str(job.updated_at),
    }

    if job.status == "complete" and job.result_json:
        response["result"] = json.loads(job.result_json)
    elif job.status == "failed":
        response["error"] = job.error_message

    return response


@router.post("/regenerate/{question_id}")
def regenerate_single(
    question_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Regenerate the answer for a single question (uses latest run)."""
    question = verify_question_ownership(question_id, user["id"], db)

    # Find the latest answer for this question owned by user
    existing = (
        db.query(Answer)
        .join(Run, Answer.run_id == Run.id)
        .filter(Answer.question_id == question_id, Run.user_id == user["id"])
        .order_by(Answer.created_at.desc())
        .first()
    )
    if not existing:
        raise HTTPException(404, "No existing answer to regenerate")

    gen = generate_answer(question.text, user_id=user["id"])

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
