"""Admin-only CSV data export (Settings → Data Export).

Per-entity CSV at /exports/{entity}.csv, or a zip of several via
/exports/bundle?types=a,b,c.
"""
import csv
import io
import zipfile
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_admin
from app.services.audit import log_audit
from app.models.user import User
from app.models.project import Project
from app.models.client import Client
from app.models.reimbursement import Reimbursement
from app.models.salary_slip import SalarySlip
from app.models.leave import LeaveRequest
from app.models.weekly_timesheet import WeeklyTimesheet
from app.models.estimate import Estimate

router = APIRouter(prefix="/exports", tags=["exports"])

ENTITIES = [
    "employees", "projects", "reimbursements", "salary-slips",
    "clients", "leaves", "timesheets", "estimates",
]


def _csv(headers, rows) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    for r in rows:
        w.writerow(["" if v is None else v for v in r])
    return buf.getvalue()


async def _user_map(db):
    return {u.id: u.name for u in (await db.execute(select(User))).scalars().all()}


async def _build(entity: str, db: AsyncSession):
    """Return (headers, rows) for one entity."""
    if entity == "employees":
        rows = (await db.execute(select(User).order_by(User.name))).scalars().all()
        h = ["id", "name", "designation", "role", "studio_email", "personal_mail",
             "phone_number", "joining_date", "end_date", "is_active", "salary_month",
             "pan_number", "aadhar_number", "bank_name", "bank_account_number"]
        return h, [[u.id, u.name, u.designation, u.role, u.studio_email, u.personal_mail,
                    u.phone_number, u.joining_date, u.end_date, u.is_active, u.salary_month,
                    u.pan_number, u.aadhar_number, u.bank_name, u.bank_account_number] for u in rows]

    if entity == "projects":
        rows = (await db.execute(select(Project).order_by(Project.project_number))).scalars().all()
        clients = {c.id: c.name for c in (await db.execute(select(Client))).scalars().all()}
        h = ["id", "project_number", "name", "display_name", "client", "location", "year",
             "current_stage", "is_billed", "start_date", "end_date", "partner_hourly_rate",
             "billed_amount", "advance_amount"]
        return h, [[p.id, p.project_number, p.name, p.display_name, clients.get(p.client_id),
                    p.location, p.year, p.current_stage, p.is_billed, p.start_date, p.end_date,
                    p.partner_hourly_rate, p.billed_amount, p.advance_amount] for p in rows]

    if entity == "clients":
        rows = (await db.execute(select(Client).order_by(Client.name))).scalars().all()
        h = ["id", "name", "customer_type", "salutation", "email", "phone", "gstin", "pan",
             "address_line1", "address_line2", "city", "state", "pincode"]
        return h, [[c.id, c.name, getattr(c, "customer_type", None), getattr(c, "salutation", None),
                    c.email, c.phone, c.gstin, getattr(c, "pan", None),
                    getattr(c, "address_line1", None), getattr(c, "address_line2", None),
                    getattr(c, "city", None), getattr(c, "state", None), getattr(c, "pincode", None)] for c in rows]

    if entity == "reimbursements":
        rows = (await db.execute(select(Reimbursement).order_by(Reimbursement.date.desc()))).scalars().all()
        um = await _user_map(db)
        h = ["id", "employee", "amount", "reason", "date", "status", "month_added"]
        return h, [[r.id, um.get(r.employee_id), r.amount, r.reason, r.date, r.status, r.month_added] for r in rows]

    if entity == "salary-slips":
        rows = (await db.execute(select(SalarySlip).order_by(SalarySlip.month.desc()))).scalars().all()
        um = await _user_map(db)
        h = ["id", "employee", "month", "base_salary", "tds_percent", "tds_amount",
             "reimbursement_total", "leave_deduction", "net_total", "payout_date", "status", "approved_at"]
        return h, [[s.id, um.get(s.employee_id), s.month, s.base_salary, s.tds_percent, s.tds_amount,
                    s.reimbursement_total, s.leave_deduction, s.net_total, s.payout_date, s.status,
                    s.approved_at.isoformat() if s.approved_at else None] for s in rows]

    if entity == "leaves":
        rows = (await db.execute(select(LeaveRequest).order_by(LeaveRequest.start_date.desc()))).scalars().all()
        um = await _user_map(db)
        h = ["id", "employee", "start_date", "end_date", "days_count", "paid_days", "unpaid_days", "status", "reason"]
        return h, [[l.id, um.get(l.employee_id), l.start_date, l.end_date, l.days_count,
                    l.paid_days, l.unpaid_days, l.status, l.reason] for l in rows]

    if entity == "timesheets":
        rows = (await db.execute(select(WeeklyTimesheet).order_by(WeeklyTimesheet.week_start.desc()))).scalars().all()
        um = await _user_map(db)
        h = ["id", "employee", "week_start", "week_end", "total_hours", "status", "submitted_at",
             "pm_approved_by", "pm_approved_at", "admin_approved_by", "admin_approved_at", "rejected_by", "rejection_reason"]
        return h, [[t.id, um.get(t.employee_id), t.week_start, t.week_end, t.total_hours, t.status,
                    t.submitted_at.isoformat() if t.submitted_at else None,
                    um.get(t.pm_approved_by), t.pm_approved_at.isoformat() if t.pm_approved_at else None,
                    um.get(t.admin_approved_by), t.admin_approved_at.isoformat() if t.admin_approved_at else None,
                    um.get(t.rejected_by), t.rejection_reason] for t in rows]

    if entity == "estimates":
        rows = (await db.execute(select(Estimate).order_by(Estimate.created_at.desc()))).scalars().all()
        um = await _user_map(db)
        h = ["id", "project_name", "start_date", "end_date", "working_days", "partner_cost",
             "team_cost", "grand_total", "status", "created_by", "created_at"]
        return h, [[e.id, e.project_name, e.start_date, e.end_date, e.working_days, e.partner_cost,
                    e.team_cost, e.grand_total, e.status, um.get(e.created_by),
                    e.created_at.isoformat() if e.created_at else None] for e in rows]

    raise HTTPException(404, "Unknown export entity")


@router.get("/bundle")
async def export_bundle(types: str, db: AsyncSession = Depends(get_db), current_user = Depends(require_admin)):
    wanted = [t.strip() for t in types.split(",") if t.strip()]
    invalid = [t for t in wanted if t not in ENTITIES]
    if invalid:
        raise HTTPException(400, f"Unknown export types: {', '.join(invalid)}")
    if not wanted:
        raise HTTPException(400, "No export types selected")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for t in wanted:
            headers, rows = await _build(t, db)
            zf.writestr(f"{t}.csv", _csv(headers, rows))

    await log_audit(db, current_user, "export.bundle", "export", None,
                    summary=f"Exported CSV bundle: {', '.join(wanted)}")
    await db.commit()
    return Response(
        content=buf.getvalue(), media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="mh02-export-{date.today()}.zip"'},
    )


@router.get("/{entity}.csv")
async def export_csv(entity: str, db: AsyncSession = Depends(get_db), current_user = Depends(require_admin)):
    if entity not in ENTITIES:
        raise HTTPException(404, "Unknown export entity")
    headers, rows = await _build(entity, db)
    await log_audit(db, current_user, f"export.{entity}", "export", None,
                    summary=f"Exported {entity} CSV ({len(rows)} rows)")
    await db.commit()
    return Response(
        content=_csv(headers, rows), media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{entity}-{date.today()}.csv"'},
    )
