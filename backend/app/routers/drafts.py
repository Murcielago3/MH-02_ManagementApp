from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sql_delete
from typing import Any, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.draft import Draft
from app.auth import get_current_user

router = APIRouter(prefix="/drafts", tags=["drafts"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class DraftIn(BaseModel):
    label: Optional[str] = None
    data: Any = {}


def serialize_draft(d: Draft) -> dict:
    return {
        "key": d.draft_key,
        "namespace": d.namespace,
        "label": d.label,
        "data": d.data if d.data is not None else {},
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }


# ── Endpoints ────────────────────────────────────────────────────────────────
# Every endpoint is scoped to the authenticated user (drafts are private to the
# account, never shared), so a user only ever sees and edits their own drafts —
# from any device they sign in on.

@router.get("/{namespace}")
async def list_drafts(
    namespace: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """All drafts in a namespace for the current user, newest first."""
    result = await db.execute(
        select(Draft)
        .where(Draft.user_id == current_user.id, Draft.namespace == namespace)
        .order_by(Draft.updated_at.desc())
    )
    return [serialize_draft(d) for d in result.scalars().all()]


@router.get("/{namespace}/{key}")
async def get_draft(
    namespace: str,
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(Draft).where(
            Draft.user_id == current_user.id,
            Draft.namespace == namespace,
            Draft.draft_key == key,
        )
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(404, "Draft not found")
    return serialize_draft(draft)


@router.put("/{namespace}/{key}")
async def upsert_draft(
    namespace: str,
    key: str,
    body: DraftIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create or update a draft. Idempotent on (user, namespace, key), so the
    frontend's autosave can call this repeatedly without creating duplicates."""
    result = await db.execute(
        select(Draft).where(
            Draft.user_id == current_user.id,
            Draft.namespace == namespace,
            Draft.draft_key == key,
        )
    )
    draft = result.scalar_one_or_none()
    if draft:
        draft.label = body.label
        draft.data = body.data
    else:
        draft = Draft(
            user_id=current_user.id,
            namespace=namespace,
            draft_key=key,
            label=body.label,
            data=body.data,
        )
        db.add(draft)
    await db.commit()
    await db.refresh(draft)
    return serialize_draft(draft)


@router.delete("/{namespace}/{key}", status_code=204)
async def delete_draft(
    namespace: str,
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a draft. Succeeds (204) even if it doesn't exist."""
    await db.execute(
        sql_delete(Draft).where(
            Draft.user_id == current_user.id,
            Draft.namespace == namespace,
            Draft.draft_key == key,
        )
    )
    await db.commit()
