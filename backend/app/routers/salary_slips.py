"""Recurring monthly salary slips.

Net pay = base_salary - tds_amount + reimbursement_total

- TDS % comes from Settings (flat rate), snapshotted onto each slip and
  editable per-slip before approval.
- Reimbursements bundled into a slip are the *approved* ones whose
  `month_added` equals the slip's month.
- Payout date is the 7th of the month following the salary month. If that 7th
  is a Sunday it defaults to the working day before (Friday); the admin can
  switch it to the working day after (Monday) or any date before approving.
- There is no background scheduler: slips are auto-generated (idempotent) for
  every completed month whenever the list is read, and can also be generated
  on demand by an admin.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date, timedelta, datetime
from decimal import Decimal
from calendar import monthrange
from pydantic import BaseModel

from app.database import get_db
from app.models.salary_slip import SalarySlip
from app.models.reimbursement import Reimbursement
from app.models.leave import LeaveRequest
from app.models.user import User
from app.auth import require_admin, require_manager, get_current_user
from app.routers.settings import get_settings_snapshot, get_or_create_settings
from app.routers.invoices import format_indian_currency
from app.services.audit import log_audit

router = APIRouter(prefix="/salary-slips", tags=["salary_slips"])

# How many months back to auto-generate slips for (keeps the work bounded).
AUTO_WINDOW_MONTHS = 14


# ─── Month / date helpers ─────────────────────────────────────────────────────
def _parse_month(month_str: str):
    y, m = month_str.split("-")
    return int(y), int(m)


def _month_str(y: int, m: int) -> str:
    return f"{y:04d}-{m:02d}"


def _add_months(y: int, m: int, delta: int):
    idx = y * 12 + (m - 1) + delta
    return idx // 12, idx % 12 + 1


def _seventh_following(month_str: str) -> date:
    """The 7th of the month after the given salary month."""
    y, m = _parse_month(month_str)
    ny, nm = _add_months(y, m, 1)
    return date(ny, nm, 7)


def _default_payout(seventh: date) -> date:
    """If the 7th is a Sunday, default to the Friday before; else the 7th."""
    if seventh.weekday() == 6:  # Sunday
        return seventh - timedelta(days=2)  # Friday
    return seventh


def _payout_meta(month_str: str) -> dict:
    """Default payout date plus before/after working-day alternatives."""
    seventh = _seventh_following(month_str)
    is_sunday = seventh.weekday() == 6
    return {
        "default": _default_payout(seventh),
        "seventh": seventh,
        "seventh_is_sunday": is_sunday,
        "before": seventh - timedelta(days=2),  # Friday
        "after": seventh + timedelta(days=1),    # Monday
    }


def _eligible_months(today: date) -> list[str]:
    """Salary months whose payout date has arrived, within the auto window."""
    months = []
    cy, cm = today.year, today.month
    for back in range(AUTO_WINDOW_MONTHS):
        y, m = _add_months(cy, cm, -back)
        ms = _month_str(y, m)
        if _default_payout(_seventh_following(ms)) <= today:
            months.append(ms)
    return months


def _q(val) -> Decimal:
    return Decimal(str(val or 0))


# ─── Generation ───────────────────────────────────────────────────────────────
async def _reimbursement_totals(db: AsyncSession, months: list[str]) -> dict:
    """Map of (employee_id, month) -> summed approved reimbursement amount."""
    if not months:
        return {}
    result = await db.execute(
        select(Reimbursement).where(
            Reimbursement.status == "approved",
            Reimbursement.month_added.in_(months),
        )
    )
    totals: dict = {}
    for r in result.scalars().all():
        key = (r.employee_id, r.month_added)
        totals[key] = totals.get(key, Decimal("0")) + _q(r.amount)
    return totals


async def reopen_month_slip(db: AsyncSession, user_id: int, month_str: str):
    """After a backdated raise, recompute that month's slip from the new salary
    and send it back to 'pending' for admin re-approval. No-op if no slip exists."""
    res = await db.execute(
        select(SalarySlip).where(SalarySlip.employee_id == user_id, SalarySlip.month == month_str)
    )
    slip = res.scalar_one_or_none()
    if slip is None:
        return
    from app.services.salary import resolve_period
    y, m = _parse_month(month_str)
    period = await resolve_period(db, user_id, date(y, m, 1))
    if period is not None and period.monthly_salary is not None:
        slip.base_salary = _q(period.monthly_salary)
    tds_amount, net = _compute(slip.base_salary, slip.tds_percent, slip.reimbursement_total, slip.leave_deduction)
    slip.tds_amount = tds_amount
    slip.net_total = net
    slip.status = "pending"
    await db.commit()


def _compute(base_salary, tds_percent, reimb_total, leave_deduction=0):
    base = _q(base_salary)
    tds_pct = _q(tds_percent)
    reimb = _q(reimb_total)
    leave_ded = _q(leave_deduction)
    tds_amount = (base * tds_pct / Decimal("100")).quantize(Decimal("0.01"))
    net = base - tds_amount + reimb - leave_ded
    return tds_amount, net


def _hourly_rate(base_salary, salary_hour, snapshot) -> Decimal:
    """Hourly rate: explicit salary_hour if set, else the settings formula
    (base * salary_months_per_year / 12) / working_hours_per_month."""
    sh = _q(salary_hour)
    if sh > 0:
        return sh
    base = _q(base_salary)
    smpy = Decimal(str(snapshot.get("salary_months_per_year", 13) or 13))
    whpm = Decimal(str(snapshot.get("working_hours_per_month", 160) or 160))
    if base <= 0 or whpm <= 0:
        return Decimal("0")
    return (base * smpy / Decimal("12")) / whpm


async def _leave_totals(db: AsyncSession, months: list[str]) -> dict:
    """Map of (employee_id, month) -> (paid_days, unpaid_days) from approved
    leaves, attributed by the leave's start-date month."""
    if not months:
        return {}
    parsed = sorted(_parse_month(m) for m in months)
    first = date(parsed[0][0], parsed[0][1], 1)
    ly, lm = parsed[-1]
    last = date(*_add_months(ly, lm, 1), 1) - timedelta(days=1)
    result = await db.execute(
        select(LeaveRequest).where(
            LeaveRequest.status == "approved",
            LeaveRequest.start_date >= first,
            LeaveRequest.start_date <= last,
        )
    )
    totals: dict = {}
    for lv in result.scalars().all():
        ms = f"{lv.start_date.year:04d}-{lv.start_date.month:02d}"
        p, u = totals.get((lv.employee_id, ms), (0, 0))
        totals[(lv.employee_id, ms)] = (p + (lv.paid_days or 0), u + (lv.unpaid_days or 0))
    return totals


async def ensure_slips(db: AsyncSession, only_month: Optional[str] = None) -> int:
    """Create missing slips (and refresh pending ones).

    Two modes:
    - Automatic (only_month=None): backfills every *eligible* completed month
      and skips employees who hadn't joined yet or have no pay that month.
    - Explicit (only_month set): a deliberate admin run for one month — every
      active employee gets a slip regardless of salary or joining date.

    Idempotent. Approved slips are never modified. Returns number created.
    """
    explicit = only_month is not None
    today = date.today()
    months = [only_month] if explicit else _eligible_months(today)
    if not months:
        return 0

    snapshot = await get_settings_snapshot(db)
    tds_percent = snapshot.get("tds_percent", 10)

    # Active employees with their joining/end dates
    users_res = await db.execute(select(User).where(User.is_active == True))  # noqa: E712
    users = users_res.scalars().all()

    # Point-in-time salary per month from salary_history; fall back to the
    # current mirror for users without history (e.g. admin/accounts).
    from app.models.salary_history import SalaryHistory
    from app.services.salary import _period_for_date
    sh_res = await db.execute(
        select(SalaryHistory)
        .where(SalaryHistory.user_id.in_([u.id for u in users]))
        .order_by(SalaryHistory.effective_from)
    )
    periods_by_user: dict = {}
    for sh in sh_res.scalars().all():
        periods_by_user.setdefault(sh.user_id, []).append(sh)

    def _month_pay(u, y, m):
        p = _period_for_date(periods_by_user.get(u.id, []), date(y, m, 1))
        if p is not None and p.monthly_salary is not None:
            return _q(p.monthly_salary), _q(p.hourly_rate)
        return _q(u.salary_month), _hourly_rate(u.salary_month, u.salary_hour, snapshot)

    # Existing slips for these months
    existing_res = await db.execute(
        select(SalarySlip).where(SalarySlip.month.in_(months))
    )
    existing = {(s.employee_id, s.month): s for s in existing_res.scalars().all()}

    reimb_totals = await _reimbursement_totals(db, months)
    leave_totals = await _leave_totals(db, months)

    created = 0
    for u in users:
        join = u.joining_date
        for ms in months:
            y, m = _parse_month(ms)
            month_end = (date(*_add_months(y, m, 1), 1) - timedelta(days=1))
            base_sal, hourly = _month_pay(u, y, m)

            reimb = reimb_totals.get((u.id, ms), Decimal("0"))
            paid_days, unpaid_days = leave_totals.get((u.id, ms), (0, 0))
            leave_ded = (hourly * Decimal("8") * Decimal(str(unpaid_days))).quantize(Decimal("0.01"))
            # A reimbursement or unpaid-leave adjustment is real money owed for the
            # month even outside the normal employment window.
            has_money = reimb > 0 or unpaid_days > 0
            out_of_window = bool(
                (join and month_end < join) or
                (u.end_date and date(y, m, 1) > u.end_date)
            )
            # In automatic mode, skip months outside employment unless there's a
            # reimbursement/leave to settle. And for any out-of-window month, never
            # pay base salary — settle only the claim (guards against e.g. a bad
            # future joining date producing a full-salary slip).
            if out_of_window and not has_money and not explicit:
                continue
            if out_of_window:
                base_sal = Decimal("0")
                leave_ded = Decimal("0")

            slip = existing.get((u.id, ms))

            # In automatic mode, don't create empty slips for accounts with no
            # pay this month (e.g. admin accounts without a salary). An explicit
            # run always creates a slip so every employee is covered.
            if slip is None and not explicit and base_sal <= 0 and reimb <= 0 and unpaid_days <= 0:
                continue

            if slip is None:
                tds_amount, net = _compute(base_sal, tds_percent, reimb, leave_ded)
                db.add(SalarySlip(
                    employee_id=u.id,
                    month=ms,
                    base_salary=_q(base_sal),
                    tds_percent=_q(tds_percent),
                    tds_amount=tds_amount,
                    reimbursement_total=reimb,
                    paid_leave_days=Decimal(str(paid_days)),
                    unpaid_leave_days=Decimal(str(unpaid_days)),
                    leave_deduction=leave_ded,
                    net_total=net,
                    payout_date=_payout_meta(ms)["default"],
                    status="pending",
                ))
                created += 1
            elif slip.status == "pending":
                # Refresh pending slip so newly-approved reimbursements / leaves flow in.
                tds_amount, net = _compute(slip.base_salary, slip.tds_percent, reimb, leave_ded)
                slip.reimbursement_total = reimb
                slip.paid_leave_days = Decimal(str(paid_days))
                slip.unpaid_leave_days = Decimal(str(unpaid_days))
                slip.leave_deduction = leave_ded
                slip.tds_amount = tds_amount
                slip.net_total = net

    if created or existing:
        await db.commit()
    return created


# ─── Serialization ────────────────────────────────────────────────────────────
def _serialize(slip: SalarySlip, employee_name: str = None) -> dict:
    meta = _payout_meta(slip.month)
    return {
        "id": slip.id,
        "employee_id": slip.employee_id,
        "employee_name": employee_name,
        "month": slip.month,
        "base_salary": float(slip.base_salary or 0),
        "tds_percent": float(slip.tds_percent or 0),
        "tds_amount": float(slip.tds_amount or 0),
        "reimbursement_total": float(slip.reimbursement_total or 0),
        "paid_leave_days": float(slip.paid_leave_days or 0),
        "unpaid_leave_days": float(slip.unpaid_leave_days or 0),
        "leave_deduction": float(slip.leave_deduction or 0),
        "net_total": float(slip.net_total or 0),
        "payout_date": slip.payout_date.isoformat() if slip.payout_date else None,
        "status": slip.status,
        "created_at": slip.created_at.isoformat() if slip.created_at else None,
        "approved_at": slip.approved_at.isoformat() if slip.approved_at else None,
        # Payout-date helpers for the admin UI
        "payout_seventh": meta["seventh"].isoformat(),
        "payout_seventh_is_sunday": meta["seventh_is_sunday"],
        "payout_before": meta["before"].isoformat(),   # Friday
        "payout_after": meta["after"].isoformat(),      # Monday
    }


async def _name_map(db: AsyncSession, employee_ids: set) -> dict:
    if not employee_ids:
        return {}
    res = await db.execute(select(User).where(User.id.in_(employee_ids)))
    return {u.id: u.name for u in res.scalars().all()}


# ─── Schemas ──────────────────────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    month: Optional[str] = None  # "YYYY-MM"; default = all eligible months


class BulkApproveRequest(BaseModel):
    ids: list[int]


class BulkTdsRequest(BaseModel):
    ids: list[int]
    tds_percent: float


class SlipUpdate(BaseModel):
    tds_percent: Optional[float] = None
    reimbursement_total: Optional[float] = None
    payout_date: Optional[date] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────
@router.get("/")
async def list_slips(
    month: Optional[str] = None,
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    await ensure_slips(db)
    query = select(SalarySlip)
    if month:
        query = query.where(SalarySlip.month == month)
    if employee_id:
        query = query.where(SalarySlip.employee_id == employee_id)
    if status:
        query = query.where(SalarySlip.status == status)
    result = await db.execute(query)
    slips = result.scalars().all()
    names = await _name_map(db, {s.employee_id for s in slips})
    slips.sort(key=lambda s: (s.month, names.get(s.employee_id, "")), reverse=True)
    return [_serialize(s, names.get(s.employee_id)) for s in slips]


@router.get("/my")
async def my_slips(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await ensure_slips(db)
    result = await db.execute(
        select(SalarySlip).where(SalarySlip.employee_id == current_user.id)
    )
    slips = result.scalars().all()
    slips.sort(key=lambda s: s.month, reverse=True)
    return [_serialize(s, current_user.name) for s in slips]


@router.get("/{slip_id}")
async def get_slip(
    slip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(SalarySlip).where(SalarySlip.id == slip_id))
    slip = result.scalar_one_or_none()
    if not slip:
        raise HTTPException(404, "Salary slip not found")
    # Employees may only view their own slips
    if current_user.role not in ("admin", "project_manager") and slip.employee_id != current_user.id:
        raise HTTPException(403, "Insufficient permissions")

    names = await _name_map(db, {slip.employee_id})
    data = _serialize(slip, names.get(slip.employee_id))

    # Attach the contributing reimbursement line items
    reimb_res = await db.execute(
        select(Reimbursement).where(
            Reimbursement.employee_id == slip.employee_id,
            Reimbursement.status == "approved",
            Reimbursement.month_added == slip.month,
        )
    )
    data["reimbursements"] = [
        {
            "id": r.id,
            "reason": r.reason,
            "amount": float(r.amount or 0),
            "date": r.date.isoformat() if r.date else None,
        }
        for r in reimb_res.scalars().all()
    ]
    return data


@router.post("/generate")
async def generate_slips(
    data: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    created = await ensure_slips(db, only_month=data.month)
    return {"created": created, "month": data.month or "all eligible"}


@router.patch("/{slip_id}")
async def update_slip(
    slip_id: int,
    data: SlipUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    result = await db.execute(select(SalarySlip).where(SalarySlip.id == slip_id))
    slip = result.scalar_one_or_none()
    if not slip:
        raise HTTPException(404, "Salary slip not found")
    if slip.status == "approved":
        raise HTTPException(400, "Approved slips cannot be edited")

    if data.tds_percent is not None:
        slip.tds_percent = _q(data.tds_percent)
    if data.reimbursement_total is not None:
        slip.reimbursement_total = _q(data.reimbursement_total)
    if data.payout_date is not None:
        slip.payout_date = data.payout_date

    tds_amount, net = _compute(slip.base_salary, slip.tds_percent, slip.reimbursement_total, slip.leave_deduction)
    slip.tds_amount = tds_amount
    slip.net_total = net

    await db.commit()
    await db.refresh(slip)
    names = await _name_map(db, {slip.employee_id})
    return _serialize(slip, names.get(slip.employee_id))


@router.patch("/{slip_id}/approve")
async def approve_slip(
    slip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    result = await db.execute(select(SalarySlip).where(SalarySlip.id == slip_id))
    slip = result.scalar_one_or_none()
    if not slip:
        raise HTTPException(404, "Salary slip not found")
    slip.status = "approved"
    slip.approved_at = datetime.utcnow()
    await log_audit(db, current_user, "salary_slip.approved", "salary_slip", slip.id,
                    summary=f"Approved salary slip for {slip.month}")
    await db.commit()
    await db.refresh(slip)
    names = await _name_map(db, {slip.employee_id})
    return _serialize(slip, names.get(slip.employee_id))


@router.post("/approve-month")
async def approve_month(
    data: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not data.month:
        raise HTTPException(400, "month is required")
    result = await db.execute(
        select(SalarySlip).where(
            SalarySlip.month == data.month,
            SalarySlip.status == "pending",
        )
    )
    slips = result.scalars().all()
    now = datetime.utcnow()
    for s in slips:
        s.status = "approved"
        s.approved_at = now
    if slips:
        await log_audit(db, current_user, "salary_slip.approved_month", "salary_slip", None,
                        summary=f"Approved {len(slips)} salary slips for {data.month}")
    await db.commit()
    return {"approved": len(slips), "month": data.month}


@router.post("/approve-bulk")
async def approve_bulk(
    data: BulkApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Approve a specific set of pending slips by id."""
    if not data.ids:
        return {"approved": 0}
    result = await db.execute(
        select(SalarySlip).where(
            SalarySlip.id.in_(data.ids),
            SalarySlip.status == "pending",
        )
    )
    slips = result.scalars().all()
    now = datetime.utcnow()
    for s in slips:
        s.status = "approved"
        s.approved_at = now
    if slips:
        await log_audit(db, current_user, "salary_slip.approved_bulk", "salary_slip", None,
                        summary=f"Approved {len(slips)} salary slips")
    await db.commit()
    return {"approved": len(slips)}


@router.post("/bulk-set-tds")
async def bulk_set_tds(
    data: BulkTdsRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Set the TDS % on a set of pending slips and recompute their totals."""
    if not data.ids:
        return {"updated": 0}
    result = await db.execute(
        select(SalarySlip).where(
            SalarySlip.id.in_(data.ids),
            SalarySlip.status == "pending",
        )
    )
    slips = result.scalars().all()
    for s in slips:
        s.tds_percent = _q(data.tds_percent)
        tds_amount, net = _compute(s.base_salary, s.tds_percent, s.reimbursement_total, s.leave_deduction)
        s.tds_amount = tds_amount
        s.net_total = net
    await db.commit()
    return {"updated": len(slips)}


# ─── PDF rendering ────────────────────────────────────────────────────────────
def _words_rupees(amount) -> str:
    """e.g. 22500 -> 'Twenty Two Thousand Five Hundred Rupees Only'."""
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
            "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
            "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy",
            "Eighty", "Ninety"]

    def under_thousand(n):
        if n == 0:
            return ""
        if n < 20:
            return ones[n]
        if n < 100:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")
        return ones[n // 100] + " Hundred" + (" " + under_thousand(n % 100) if n % 100 else "")

    n = int(round(float(amount or 0)))
    if n == 0:
        return "Zero Rupees Only"
    crore = n // 10000000; n %= 10000000
    lakh = n // 100000; n %= 100000
    thousand = n // 1000; n %= 1000
    rest = n
    parts = []
    if crore:
        parts.append(under_thousand(crore) + " Crore")
    if lakh:
        parts.append(under_thousand(lakh) + " Lakh")
    if thousand:
        parts.append(under_thousand(thousand) + " Thousand")
    if rest:
        parts.append(under_thousand(rest))
    return " ".join(parts) + " Rupees Only"


def _money(v) -> str:
    return "&#8377; " + format_indian_currency(float(v or 0))


def _logo_data_uri() -> str:
    import base64, os
    logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "static", "logo.jpg")
    try:
        with open(logo_path, "rb") as f:
            return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
    except Exception:
        return "static/logo.jpg"


def render_salary_slip_html(slip, employee, settings, reimb_total) -> str:
    y, m = _parse_month(slip.month)
    calendar_days = monthrange(y, m)[1]
    # Working days = Mon–Fri count in the month
    working_days = sum(
        1 for d in range(1, calendar_days + 1)
        if date(y, m, d).weekday() < 5
    )
    paid_leaves = float(slip.paid_leave_days or 0)
    unpaid_leaves = float(slip.unpaid_leave_days or 0)
    leave_deduction = float(slip.leave_deduction or 0)
    # Trim trailing .0 for whole-day counts
    def _days(v):
        return int(v) if float(v).is_integer() else v
    total_pay_days = _days(calendar_days - unpaid_leaves)

    base = float(slip.base_salary or 0)
    reimb = float(reimb_total or 0)
    gross = base + reimb
    tds_pct = float(slip.tds_percent or 0)
    tds_amount = float(slip.tds_amount or 0)
    total_deductions = tds_amount + leave_deduction
    net = float(slip.net_total or 0)

    pay_period = date(y, m, 1).strftime("%b-%y")           # "May-26"
    pay_date = (f"{slip.payout_date.month}/{slip.payout_date.day}/{slip.payout_date.year}"
                if slip.payout_date else "")
    doj = employee.joining_date.strftime("%d %b %Y") if employee.joining_date else ""
    tds_pct_label = f"{tds_pct:g}"

    company_name = (settings.company_name if settings and settings.company_name else "Studio MH02 LLP").upper()
    company_address = (settings.company_address if settings and settings.company_address
                       else "201, Prathamesh Apartments, Mahant Road, Vile Parle (East), Mumbai – 400057")
    company_address_html = company_address.replace("\n", ", ")
    company_email = (settings.company_email if settings and settings.company_email else "accounts@studiomh02.com")
    logo_src = _logo_data_uri()

    # ── Earnings rows (Basic + fixed template rows + optional Reimbursements) ──
    earn_rows = [
        ("Basic", _money(base), _money(base)),
        ("Allowance", _money(0), _money(0)),
        ("Other Allowance", _money(0), _money(0)),
        ("Bonus", _money(0), _money(0)),
    ]
    if reimb > 0:
        earn_rows.append(("Reimbursements", "", _money(reimb)))

    # ── Deductions rows (TDS, then unpaid-leave cut if any) ──
    ded_rows = [(f"TDS {tds_pct_label}%", _money(tds_amount))]
    if unpaid_leaves > 0:
        ded_rows.append((f"Unpaid Leave ({_days(unpaid_leaves)} day{'s' if unpaid_leaves != 1 else ''})", _money(leave_deduction)))

    # Pad both sides to equal length so the table is balanced
    n_rows = max(len(earn_rows), len(ded_rows), 4)
    while len(earn_rows) < n_rows:
        earn_rows.append(("", "", ""))
    while len(ded_rows) < n_rows:
        ded_rows.append(("", ""))

    body_rows = ""
    for (e_label, e_rate, e_cur), (d_label, d_cur) in zip(earn_rows, ded_rows):
        body_rows += f"""
        <tr>
          <td class="cell">{e_label}</td>
          <td class="cell num">{e_rate}</td>
          <td class="cell num">{e_cur}</td>
          <td class="cell">{d_label}</td>
          <td class="cell num">{d_cur}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @page {{ size: A4; margin: 14mm; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: Arial, Helvetica, sans-serif; font-size: 12px; color: #000; }}

  /* Header */
  .header {{ display: flex; align-items: flex-start; gap: 18px; margin-bottom: 26px; }}
  .logo {{ width: 96px; height: 96px; object-fit: contain; flex-shrink: 0; }}
  .head-right {{ flex: 1; }}
  .company {{ font-size: 22px; font-weight: bold; color: #287475; letter-spacing: 0.5px;
              border-bottom: 1.5px solid #000; padding-bottom: 8px; margin-bottom: 6px; }}
  .addr {{ font-size: 12px; line-height: 1.5; }}

  /* Info block */
  .info {{ width: 100%; border-collapse: collapse; margin-bottom: 22px; }}
  .info td {{ padding: 3px 0; font-size: 12px; vertical-align: top; }}
  .info .lbl {{ width: 16%; }}
  .info .val {{ width: 34%; }}

  /* Tables */
  table.grid {{ width: 100%; border-collapse: collapse; margin-bottom: 16px; }}
  table.grid td, table.grid th {{ border: 1px solid #000; padding: 5px 8px; font-size: 12px; }}
  table.grid th {{ text-align: left; font-weight: bold; }}
  .num {{ text-align: right; }}
  .days td {{ text-align: right; }}
  .days th {{ text-align: left; }}

  .cell {{ height: 22px; }}
  .row-head td {{ font-weight: bold; }}
  .totals td {{ font-weight: bold; }}

  .netbox {{ width: 100%; border-collapse: collapse; margin-bottom: 14px; }}
  .netbox td {{ border: 1px solid #000; padding: 7px 10px; font-size: 12px; }}
  .netbox .nlbl {{ width: 18%; font-weight: bold; }}

  .footer {{ display: flex; justify-content: space-between; margin-top: 60px; }}
  .footer .bold {{ font-weight: bold; }}
</style>
</head>
<body>
  <div class="header">
    <img src="{logo_src}" class="logo" alt="Logo"/>
    <div class="head-right">
      <div class="company">{company_name}</div>
      <div class="addr">{company_address_html}<br>Email: {company_email}</div>
    </div>
  </div>

  <table class="info">
    <tr>
      <td class="lbl">Pay Period</td><td class="val">{pay_period}</td>
      <td class="lbl">Pay Date</td><td class="val">{pay_date}</td>
    </tr>
    <tr>
      <td class="lbl">Name:</td><td class="val">{employee.name or ''}</td>
      <td class="lbl">Bank Name:</td><td class="val">{employee.bank_name or ''}</td>
    </tr>
    <tr>
      <td class="lbl">Designation:</td><td class="val">{employee.designation or ''}</td>
      <td class="lbl">A/C No.:</td><td class="val">{employee.bank_account_number or ''}</td>
    </tr>
    <tr>
      <td class="lbl">Emp DOJ:</td><td class="val">{doj}</td>
      <td class="lbl">Gender:</td><td class="val">{employee.gender or ''}</td>
    </tr>
    <tr>
      <td class="lbl">Location:</td><td class="val">{employee.location or ''}</td>
      <td class="lbl">Emp PAN:</td><td class="val">{employee.pan_number or ''}</td>
    </tr>
  </table>

  <table class="grid days">
    <tr class="row-head">
      <th>CALENDAR DAYS</th><th>WORKING DAYS</th><th>PAID LEAVES</th>
      <th>UNPAID LEAVES</th><th>TOTAL PAY DAYS</th>
    </tr>
    <tr>
      <td>{calendar_days}</td><td>{working_days}</td><td>{_days(paid_leaves)}</td>
      <td>{_days(unpaid_leaves)}</td><td>{total_pay_days}</td>
    </tr>
  </table>

  <table class="grid">
    <tr class="row-head">
      <td>EARNINGS</td><td>RATE</td><td>CURRENT MONTH</td>
      <td>DEDUCTIONS</td><td>CURRENT MONTH</td>
    </tr>
    {body_rows}
    <tr class="totals">
      <td>GROSS EARNINGS</td><td></td><td class="num">{_money(gross)}</td>
      <td>TOTAL DEDUCTIONS</td><td class="num">{_money(total_deductions)}</td>
    </tr>
  </table>

  <table class="netbox">
    <tr>
      <td class="nlbl">NET PAY (Rs.)</td>
      <td>{_money(net)}</td>
    </tr>
  </table>

  <table class="netbox">
    <tr>
      <td class="nlbl">NET PAY (Rs.)<br>(In Words)</td>
      <td>{_words_rupees(net)}</td>
    </tr>
  </table>

  <div class="footer">
    <div>
      <div>Accounts Team</div>
      <div class="bold">{settings.company_name if settings and settings.company_name else 'Studio MH02 LLP'}</div>
    </div>
    <div class="bold" style="align-self: flex-end;">Employee Signature</div>
  </div>
</body>
</html>"""


@router.get("/{slip_id}/pdf")
async def salary_slip_pdf(
    slip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(SalarySlip).where(SalarySlip.id == slip_id))
    slip = result.scalar_one_or_none()
    if not slip:
        raise HTTPException(404, "Salary slip not found")
    if current_user.role not in ("admin", "project_manager") and slip.employee_id != current_user.id:
        raise HTTPException(403, "Insufficient permissions")

    emp_res = await db.execute(select(User).where(User.id == slip.employee_id))
    employee = emp_res.scalar_one_or_none()
    if not employee:
        raise HTTPException(404, "Employee not found")

    try:
        settings = await get_or_create_settings(db)
        html = render_salary_slip_html(slip, employee, settings, slip.reimbursement_total)
        from weasyprint import HTML
        pdf_bytes = HTML(string=html, base_url="http://127.0.0.1:8000").write_pdf()
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Raise as HTTPException so the response still flows through CORS middleware
        # (an unhandled 500 would drop CORS headers and surface as a CORS error).
        raise HTTPException(500, f"Failed to generate salary slip PDF: {e}")

    safe_name = "".join(c if c.isalnum() else "_" for c in (employee.name or "employee"))
    fname = f"salary_slip_{safe_name}_{slip.month}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )
