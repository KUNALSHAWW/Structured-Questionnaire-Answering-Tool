"""Export router – generate downloadable XLSX or PDF for a run."""

import json
import re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import get_current_user
from app.models.models import Run, Questionnaire
from app.config import EXPORTS_DIR

router = APIRouter()


def _safe_download_name(filename: str, ext: str) -> str:
    """Sanitise questionnaire filename for use as download name."""
    stem = Path(filename).stem if filename else "export"
    stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", stem)[:80]
    return f"answers_{stem}.{ext}"


@router.get("/{run_id}")
def export_run(
    run_id: str,
    format: str = "xlsx",
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = db.query(Run).filter(Run.id == run_id, Run.user_id == user["id"]).first()
    if not run:
        raise HTTPException(404, "Run not found")

    q = db.query(Questionnaire).filter(Questionnaire.id == run.questionnaire_id).first()
    # Stable ordering by question index
    answers = sorted(run.answers, key=lambda a: (a.question.index if a.question else 0))

    if format == "xlsx":
        return _export_xlsx(run_id, q, answers)
    elif format == "pdf":
        return _export_pdf(run_id, q, answers)
    else:
        raise HTTPException(400, "Unsupported format. Use xlsx or pdf.")


def _export_xlsx(run_id, questionnaire, answers):
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Answers"
    ws.append(["#", "Question", "Answer", "Citations", "Evidence", "Confidence"])

    for a in answers:
        cits = json.loads(a.citations) if a.citations else []
        evs = json.loads(a.evidence_snippets) if a.evidence_snippets else []
        ws.append([
            a.question.index,
            a.question.text,
            a.answer_text,
            "; ".join(cits),
            "; ".join(evs)[:500],
            a.confidence_score,
        ])

    # Auto-width
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)

    filepath = EXPORTS_DIR / f"{run_id}.xlsx"
    wb.save(str(filepath))
    return FileResponse(
        str(filepath),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=_safe_download_name(questionnaire.filename, "xlsx"),
    )


def _export_pdf(run_id, questionnaire, answers):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    filepath = EXPORTS_DIR / f"{run_id}.pdf"
    doc = SimpleDocTemplate(str(filepath), pagesize=A4)
    styles = getSampleStyleSheet()
    bold = ParagraphStyle("Bold", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11)
    normal = styles["Normal"]

    story = []
    story.append(Paragraph(f"Questionnaire Answers – {questionnaire.filename}", styles["Title"]))
    story.append(Spacer(1, 12))

    for a in answers:
        cits = json.loads(a.citations) if a.citations else []
        evs = json.loads(a.evidence_snippets) if a.evidence_snippets else []

        story.append(Paragraph(f"Q{a.question.index}: {a.question.text}", bold))
        story.append(Paragraph(f"<b>Answer:</b> {a.answer_text}", normal))
        if cits:
            story.append(Paragraph(f"<b>Citations:</b> {'; '.join(cits)}", normal))
        if evs:
            snippet = evs[0][:300] if evs else ""
            story.append(Paragraph(f"<b>Evidence:</b> \"{snippet}\"", normal))
        story.append(Paragraph(f"<b>Confidence:</b> {a.confidence_score}%", normal))
        story.append(Spacer(1, 10))

    doc.build(story)
    return FileResponse(
        str(filepath),
        media_type="application/pdf",
        filename=_safe_download_name(questionnaire.filename, "pdf"),
    )
