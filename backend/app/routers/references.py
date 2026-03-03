"""References router – snippet endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import get_current_user
from app.models.models import Reference, Passage
from app.auth_utils import verify_reference_ownership

router = APIRouter()


@router.get("/{ref_id}/snippet")
def get_snippet(
    ref_id: str,
    passage_id: str = "",
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a specific passage snippet by passage_id or first passage of reference."""
    ref = verify_reference_ownership(ref_id, user["id"], db)

    if passage_id:
        passage = db.query(Passage).filter(
            Passage.id == passage_id, Passage.reference_id == ref_id
        ).first()
    else:
        passage = db.query(Passage).filter(Passage.reference_id == ref_id).first()

    if not passage:
        raise HTTPException(404, "Passage not found")

    return {
        "passage_id": passage.id,
        "reference_id": ref.id,
        "filename": ref.filename,
        "page_or_para": passage.page_or_para,
        "text": passage.text[:300],
    }
