"""Shared ownership verification helpers to prevent IDOR vulnerabilities."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Answer, Run, Reference, Question, Questionnaire, Passage


def verify_answer_ownership(answer_id: str, user_id: str, db: Session) -> Answer:
    """Return the Answer if it belongs to the user (via Run), else raise 404."""
    ans = (
        db.query(Answer)
        .join(Run, Answer.run_id == Run.id)
        .filter(Answer.id == answer_id, Run.user_id == user_id)
        .first()
    )
    if not ans:
        raise HTTPException(404, "Answer not found")
    return ans


def verify_run_ownership(run_id: str, user_id: str, db: Session) -> Run:
    """Return the Run if it belongs to the user, else raise 404."""
    run = db.query(Run).filter(Run.id == run_id, Run.user_id == user_id).first()
    if not run:
        raise HTTPException(404, "Run not found")
    return run


def verify_reference_ownership(ref_id: str, user_id: str, db: Session) -> Reference:
    """Return the Reference if it belongs to the user, else raise 404."""
    ref = db.query(Reference).filter(Reference.id == ref_id, Reference.user_id == user_id).first()
    if not ref:
        raise HTTPException(404, "Reference not found")
    return ref


def verify_question_ownership(question_id: str, user_id: str, db: Session) -> Question:
    """Return the Question if it belongs to the user (via Questionnaire), else raise 404."""
    question = (
        db.query(Question)
        .join(Questionnaire, Question.questionnaire_id == Questionnaire.id)
        .filter(Question.id == question_id, Questionnaire.user_id == user_id)
        .first()
    )
    if not question:
        raise HTTPException(404, "Question not found")
    return question


def verify_questionnaire_ownership(q_id: str, user_id: str, db: Session) -> Questionnaire:
    """Return the Questionnaire if it belongs to the user, else raise 404."""
    q = db.query(Questionnaire).filter(
        Questionnaire.id == q_id, Questionnaire.user_id == user_id
    ).first()
    if not q:
        raise HTTPException(404, "Questionnaire not found")
    return q
