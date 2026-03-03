"""Index router – build FAISS index from stored references."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import get_current_user
from app.models.models import Reference, Passage
from app.services.parser import extract_reference_text
from app.services.splitter import split_into_passages
from app.services.embeddings import build_faiss_index

router = APIRouter()


@router.post("/build")
def build_index(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Split all user references into passages, compute embeddings, build FAISS index."""
    refs = db.query(Reference).filter(Reference.user_id == user["id"]).all()
    if not refs:
        raise HTTPException(400, "No reference documents uploaded yet.")

    # Clear old passages for this user's refs
    ref_ids = [r.id for r in refs]
    db.query(Passage).filter(Passage.reference_id.in_(ref_ids)).delete(synchronize_session=False)
    db.commit()

    all_passages_meta: list[dict] = []

    for ref in refs:
        text = extract_reference_text(ref.stored_path, ref.file_type)
        chunks = split_into_passages(text, ref.filename)

        for chunk in chunks:
            p = Passage(
                reference_id=ref.id,
                text=chunk["text"],
                page_or_para=chunk["page_or_para"],
                token_count=chunk["token_count"],
            )
            db.add(p)
            db.flush()

            all_passages_meta.append(
                {
                    "passage_id": p.id,
                    "reference_id": ref.id,
                    "text": chunk["text"],
                    "page_or_para": chunk["page_or_para"],
                    "filename": ref.filename,
                }
            )

    db.commit()

    # Build FAISS
    num_indexed = build_faiss_index(all_passages_meta)

    # Optional: sync to Sanity if enabled
    _sync_sanity(refs, all_passages_meta)

    return {
        "message": "Index built successfully",
        "num_references": len(refs),
        "num_passages": len(all_passages_meta),
        "num_vectors": num_indexed,
    }


def _sync_sanity(refs, passages_meta):
    """If Sanity is enabled, push reference metadata to Sanity via HTTP API."""
    from app.config import SANITY_ENABLED, SANITY_PROJECT_ID, SANITY_TOKEN, SANITY_DATASET

    if not SANITY_ENABLED:
        return

    import httpx
    import logging

    logger = logging.getLogger(__name__)

    url = f"https://{SANITY_PROJECT_ID}.api.sanity.io/v2023-01-01/data/mutate/{SANITY_DATASET}"
    headers = {"Authorization": f"Bearer {SANITY_TOKEN}", "Content-Type": "application/json"}

    mutations = []
    for ref in refs:
        mutations.append(
            {
                "createOrReplace": {
                    "_id": f"ref-{ref.id}",
                    "_type": "reference_doc",
                    "filename": ref.filename,
                    "file_type": ref.file_type,
                    "num_passages": sum(
                        1 for p in passages_meta if p["reference_id"] == ref.id
                    ),
                }
            }
        )

    try:
        resp = httpx.post(url, json={"mutations": mutations}, headers=headers, timeout=15)
        resp.raise_for_status()
        logger.info("Synced %d references to Sanity", len(refs))
    except Exception as e:
        logger.warning("Sanity sync failed: %s", e)
