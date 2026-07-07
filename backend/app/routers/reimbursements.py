from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date
from pydantic import BaseModel
from app.database import get_db
from app.models.reimbursement import Reimbursement
from app.models.user import User
from app.auth import get_current_user, require_admin, require_manager
from app.services.slack import notify_event, lookup_user_id
from app.services.audit import log_audit
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
    background_tasks: BackgroundTasks,
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
    await db.flush()
    await log_audit(db, current_user, "reimbursement.submitted", "reimbursement", entry.id,
                    summary=f"{current_user.name} submitted reimbursement of ₹{amount:,.0f} for {reason}")
    await db.commit()
    await db.refresh(entry)

    # Notify accounts/admin in Slack (fires after the response; never blocks it).
    # Tag the submitter so Slack emails them the confirmation.
    def _notify_reimbursement_submitted(user, amount, reason, date):
        tag = f"<@{uid}>" if (uid := lookup_user_id(user.studio_email) or lookup_user_id(user.personal_mail)) else f"*{user.name}*"
        notify_event(
            "reimbursement",
            f"💸 *Reimbursement submitted*\n"
            f"{tag} — ₹{amount:,.0f} for _{reason}_ (dated {date})",
        )
    background_tasks.add_task(_notify_reimbursement_submitted, current_user, amount, reason, date)
    return entry

@router.patch("/{reimbursement_id}/action")
async def action_reimbursement(
    reimbursement_id: int,
    data: ReimbursementAction,
    background_tasks: BackgroundTasks,
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
        # Bundle into the salary slip for the month of the *expense date*. That
        # slip pays out the following month — e.g. a June-dated bill rides June's
        # slip, received ~Jul 7. The expense date is the reliable, admin-visible
        # month for a claim (submission timestamps weren't recorded historically).
        basis = entry.date or (entry.created_at.date() if entry.created_at else date.today())
        entry.month_added = basis.strftime("%Y-%m")

    emp_name = (await db.execute(select(User.name).where(User.id == entry.employee_id))).scalar_one_or_none() or "employee"
    await log_audit(db, current_user, f"reimbursement.{data.status}", "reimbursement", entry.id,
                    summary=f"{data.status.capitalize()} {emp_name}'s reimbursement of ₹{float(entry.amount):,.0f}")
    await db.commit()
    await db.refresh(entry)

    # Notify accounts/admin in Slack of the decision — tag the employee.
    emp = (await db.execute(
        select(User).where(User.id == entry.employee_id)
    )).scalar_one_or_none()
    def _notify_reimbursement_decision(emp, entry, status):
        if emp:
            uid = lookup_user_id(emp.studio_email) or lookup_user_id(emp.personal_mail)
            tag = f"<@{uid}>" if uid else f"*{emp.name}*"
        else:
            tag = f"*Employee #{entry.employee_id}*"
        verb = "approved ✅" if status == "approved" else "rejected ❌"
        notify_event(
            "reimbursement_decision",
            f"💰 Reimbursement *{verb}* — {tag}: ₹{float(entry.amount):,.0f} for _{entry.reason}_",
        )
    background_tasks.add_task(_notify_reimbursement_decision, emp, entry, data.status)
    return entry