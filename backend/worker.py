"""Background worker – processes generation jobs from the jobs table.

Usage:
    cd backend
    python worker.py

The worker polls the jobs table for pending jobs, processes them, and updates status.
"""

import json
import logging
import sys
import time
import traceback
from datetime import datetime, timezone

# Ensure backend is importable
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base
from app.models.models import Job, Questionnaire, Question, Run, Answer
from app.services.generation import generate_answer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WORKER] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

POLL_INTERVAL = int(os.getenv("WORKER_POLL_INTERVAL", "2"))  # seconds


def process_generate_job(job_id: str, payload: dict):
    """Process a 'generate' job: retrieve + answer all questions in the questionnaire."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error("Job %s not found", job_id)
            return

        job.status = "running"
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        questionnaire_id = payload["questionnaire_id"]
        user_id = job.user_id

        q = db.query(Questionnaire).filter(
            Questionnaire.id == questionnaire_id,
            Questionnaire.user_id == user_id,
        ).first()
        if not q:
            raise ValueError(f"Questionnaire {questionnaire_id} not found for user {user_id}")

        questions = sorted(q.questions, key=lambda x: x.index)
        if not questions:
            raise ValueError("No questions in questionnaire")

        # Create run
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

        result_data = {
            "run_id": run.id,
            "questionnaire_id": q.id,
            "num_answers": len(results),
            "answers": results,
        }

        job.status = "complete"
        job.result_json = json.dumps(result_data)
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info("Job %s complete: %d answers generated", job_id, len(results))

    except Exception as e:
        logger.error("Job %s failed: %s", job_id, e)
        traceback.print_exc()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)[:500]
                job.updated_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def poll_and_process():
    """Main worker loop: poll for pending jobs and process them."""
    logger.info("Worker started. Polling every %ds...", POLL_INTERVAL)

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    while True:
        db = SessionLocal()
        try:
            job = (
                db.query(Job)
                .filter(Job.status == "pending")
                .order_by(Job.created_at)
                .first()
            )
            if job:
                logger.info("Processing job %s (type=%s)", job.id, job.type)
                payload = json.loads(job.payload_json) if job.payload_json else {}
                db.close()

                if job.type == "generate":
                    process_generate_job(job.id, payload)
                else:
                    logger.warning("Unknown job type: %s", job.type)
            else:
                db.close()
        except Exception as e:
            logger.error("Worker poll error: %s", e)
            try:
                db.close()
            except Exception:
                pass

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    poll_and_process()
