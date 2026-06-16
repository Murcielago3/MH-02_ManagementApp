from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date
from pydantic import BaseModel
from app.database import get_db
from app.models.reimbursement import Reimbursement
from app.auth import get_current_user, require_admin, require_manager
import os, uuid

router = APIRouter(prefix="/reimbursements", tags=["reimbursements"])

UPLOAD_DIR = "static/uploads/reimbursements"

class ReimbursementCreate(BaseModel):
    amount: float
    reason: str
    date: date

class ReimbursementAction(BaseModel):
    status: str

@router.get("/")
async def list_reimbursements(
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    query = select(Reimbursement)
    if employee_id:
        query = query.where(Reimbursement.employee_id == employee_id)
    if status:
        query = query.where(Reimbursement.status == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/my")
async def my_reimbursements(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(select(Reimbursement).where(Reimbursement.employee_id == current_user.id))
    return result.scalars().all()

@router.post("/", status_code=201)
async def create_reimbursement(
    amount: float = Form(...),
    reason: str = Form(...),
    date: date = Form(...),
    proof: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    proof_url = None
    if proof:
        allowed = {"application/pdf", "image/jpeg", "image/jpg", "image/png"}
        if proof.content_type not in allowed:
            raise HTTPException(400, "Only PDF or image files allowed")
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(proof.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            f.write(proof.file.read())
        proof_url = f"/static/uploads/reimbursements/{filename}"
    
    entry = Reimbursement(
        employee_id=current_user.id,
        amount=amount,
        reason=reason,
        date=date,
        proof_url=proof_url
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry

@router.patch("/{reimbursement_id}/action")
async def action_reimbursement(
    reimbursement_id: int,
    data: ReimbursementAction,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    if data.status not in ["approved", "rejected"]:
        raise HTTPException(400, "Status must be approved or rejected")
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(404, "Reimbursement not found")
    
    from datetime import datetime
    entry.status = data.status
    if data.status == "approved":
        entry.month_added = datetime.now().strftime("%Y-%m")

    await db.commit()
    await db.refresh(entry)
    return entry