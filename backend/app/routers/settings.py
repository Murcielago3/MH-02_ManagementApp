"""Admin-configurable app settings (singleton row, id=1)."""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.settings import Settings
from app.auth import require_admin
from app.utils.cache import TTLCache


router = APIRouter(prefix="/settings", tags=["settings"])

# Cache for the *plain dict* derived from settings. We do NOT cache the ORM
# row (session-bound). Used by /settings GET and by the project endpoints'
# rate-params helper. Invalidated on every PATCH.
_settings_dict_cache = TTLCache(ttl_seconds=300)  # 5 min


# ─── Sensible defaults (also the seed values inserted on first read) ───
DEFAULTS = {
    "company_name": "Studio MH02 LLP",
    "company_address": "201, Prathamesh Apt, Mahant Road, Vile Parle East\nMumbai, Maharashtra 400507",
    "company_gstin": "27AEQFS5715Q1Z1",
    "company_phone": "9769911588",
    "company_email": "INFO@STUDIOMH02.COM",
    "company_signatory_name": "Srujan Gadgil",
    "company_signatory_role": "Partner",
    "working_hours_per_month": 160,
    "salary_months_per_year": 13,
    "tds_percent": 10,
}


class SettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_gstin: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    company_signatory_name: Optional[str] = None
    company_signatory_role: Optional[str] = None
    working_hours_per_month: Optional[float] = None
    salary_months_per_year: Optional[float] = None
    tds_percent: Optional[float] = None


async def get_or_create_settings(db: AsyncSession) -> Settings:
    """Always returns the singleton settings row, seeding defaults if missing."""
    result = await db.execute(select(Settings).where(Settings.id == 1))
    row = result.scalar_one_or_none()
    if row is None:
        row = Settings(id=1, **DEFAULTS)
        db.add(row)
        await db.commit()
        await db.refresh(row)
    else:
        # Backfill any missing columns from defaults so reads always have a value
        dirty = False
        for k, v in DEFAULTS.items():
            if getattr(row, k, None) in (None, ""):
                setattr(row, k, v)
                dirty = True
        if dirty:
            await db.commit()
            await db.refresh(row)
    return row


def settings_dict(s: Settings) -> dict:
    """Serialise a Settings row to a JSON-friendly dict (Numeric → float)."""
    return {
        "company_name": s.company_name,
        "company_address": s.company_address,
        "company_gstin": s.company_gstin,
        "company_phone": s.company_phone,
        "company_email": s.company_email,
        "company_signatory_name": s.company_signatory_name,
        "company_signatory_role": s.company_signatory_role,
        "working_hours_per_month": float(s.working_hours_per_month or DEFAULTS["working_hours_per_month"]),
        "salary_months_per_year": float(s.salary_months_per_year or DEFAULTS["salary_months_per_year"]),
        "tds_percent": float(s.tds_percent if s.tds_percent is not None else DEFAULTS["tds_percent"]),
    }


async def get_settings_snapshot(db: AsyncSession) -> dict:
    """
    Cached, plain-dict view of settings. Use this from any read path that just
    needs the *values* (rate params, company info for rendering, etc.).
    The /settings/ PATCH endpoint invalidates this cache.
    """
    cached = _settings_dict_cache.get("snapshot")
    if cached is not None:
        return cached
    s = await get_or_create_settings(db)
    snapshot = settings_dict(s)
    _settings_dict_cache.set("snapshot", snapshot)
    return snapshot


@router.get("/")
async def get_settings(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    # Browser may cache this for 30s; the settings page rarely changes mid-session.
    response.headers["Cache-Control"] = "private, max-age=30"
    return await get_settings_snapshot(db)


@router.patch("/")
async def update_settings(
    data: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    s = await get_or_create_settings(db)
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(s, field, value)
    await db.commit()
    await db.refresh(s)
    _settings_dict_cache.invalidate()  # cache busted on every mutation
    # smpy/whpm changes flow into reserve calculation — drop that cache too
    from app.routers.projects import _invalidate_reserve
    _invalidate_reserve()
    return settings_dict(s)
