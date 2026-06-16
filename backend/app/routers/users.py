from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date
import json, uuid, os, shutil
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.auth import get_current_user, require_admin, require_manager, hash_password

router = APIRouter(prefix="/users", tags=["users"])

STATIC_DIR = "static"
PHOTOS_DIR = os.path.join(STATIC_DIR, "uploads", "photos")
DOCS_DIR   = os.path.join(STATIC_DIR, "uploads", "documents")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_DOC_TYPES   = {"application/pdf", "image/jpeg", "image/png"}

#----SCHEMA----
class UserCreate(BaseModel):
    name: str
    designation: str
    studio_email: str
    personal_mail: str
    password: str
    role: str = "employee"
    joining_date: date
    end_date: Optional[date] = None
    salary_month: Optional[float] = None
    salary_hour: Optional[float] = None
    leaves_allowed: int = 18
    paid_leave_balance: Optional[float] = None
    pan_number: str
    aadhar_number: str
    gender: Optional[str] = None
    location: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    manager_id: Optional[int] = None
    photo_url: Optional[str] = None
    documents_url: Optional[str] = None
    time_tracker_login: Optional[str] = None
    time_tracker_password: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    studio_email: Optional[str] = None
    personal_mail: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    joining_date: Optional[date] = None
    end_date: Optional[date] = None
    salary_month: Optional[float] = None
    salary_hour: Optional[float] = None
    leaves_allowed: Optional[int] = None
    paid_leave_balance: Optional[float] = None
    pan_number: Optional[str] = None
    aadhar_number: Optional[str] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None
    photo_url: Optional[str] = None
    documents_url: Optional[str] = None
    time_tracker_login: Optional[str] = None
    time_tracker_password: Optional[str] = None

#----ROUTES----

@router.get("/")
async def list_users(
    response: Response,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db)
):
    # The employee roster is read by many views; salary/profile changes
    # propagate within 20s. Trade-off for fewer round-trips.
    response.headers["Cache-Control"] = "private, max-age=20"
    result = await db.execute(
        select(User)
        .where(User.is_active == True)
        .order_by(User.id.desc())
    )
    users = result.scalars().all()
    return users

@router.get("/me")
async def get_my_profile(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Keep the paid-leave balance current (idempotent monthly accrual)
    from app.routers.leaves import accrue_all
    await accrue_all(db)
    await db.refresh(current_user)
    # AppLayout calls this on every page mount — short cache covers session navigation
    response.headers["Cache-Control"] = "private, max-age=60"
    return current_user

@router.get("/{user_id}")
async def get_user(
    user_id: int,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db)
):
    from app.routers.leaves import accrue_all
    await accrue_all(db)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    existing = await db.execute(select(User).where(User.studio_email == data.studio_email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User with this studio email already exists")
    
    user = User(
        name=data.name,
        designation=data.designation,
        studio_email=data.studio_email,
        personal_mail=data.personal_mail,
        hashed_password=hash_password(data.password),
        role=data.role,
        joining_date=data.joining_date,
        end_date=data.end_date,
        salary_month=data.salary_month,
        salary_hour=data.salary_hour,
        leaves_allowed=data.leaves_allowed,
        paid_leave_balance=data.paid_leave_balance or 0,
        pan_number=data.pan_number,
        aadhar_number=data.aadhar_number,
        gender=data.gender,
        location=data.location,
        bank_name=data.bank_name,
        bank_account_number=data.bank_account_number,
        phone_number=data.phone_number,
        emergency_contact_number=data.emergency_contact_number,
        emergency_contact_relationship=data.emergency_contact_relationship,
        manager_id=data.manager_id,
        time_tracker_login=data.time_tracker_login,
        time_tracker_password=data.time_tracker_password,
        documents_url="[]"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.patch("/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Authorization: Admins/Managers can edit anyone. Employees can edit only themselves.
    is_self = current_user.id == user_id
    is_manager = current_user.role in ("admin", "project_manager")
    is_admin = current_user.role == "admin"

    if not is_self and not is_manager:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Restrict fields for employees (non-managers)
    if not is_manager:
        sensitive_fields = {
            "role", "joining_date", "end_date", "salary_month", "salary_hour",
            "leaves_allowed", "paid_leave_balance", "pan_number", "aadhar_number",
            "manager_id", "is_active"
        }
        for field in sensitive_fields:
            if field in update_data:
                del update_data[field]

    salary_changed = ("salary_month" in update_data) or ("salary_hour" in update_data)

    for field, value in update_data.items():
        if field == "password" and value:
            setattr(user, "hashed_password", hash_password(value))
        else:
            setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    # A salary change ripples into every project's reserve balance.
    if salary_changed:
        from app.routers.projects import _invalidate_reserve
        _invalidate_reserve()
    return user
    
@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    await db.commit()

# ── File Upload Endpoints ──

@router.post("/{user_id}/upload-photo")
async def upload_photo(
    user_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload or replace a profile photo for the given user."""
    # Only admin/manager can upload for others; employees can upload for themselves
    if current_user.id != user_id and current_user.role not in ("admin", "project_manager"):
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed. Use JPEG, PNG, or WebP.")

    # Delete old photo if it exists
    if user.photo_url:
        old_path = os.path.join(STATIC_DIR, *user.photo_url.split("/static/", 1)[-1].split("/"))
        if os.path.exists(old_path):
            os.remove(old_path)

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
    save_path = os.path.join(PHOTOS_DIR, filename)

    os.makedirs(PHOTOS_DIR, exist_ok=True)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    photo_url = f"/static/uploads/photos/{filename}"
    user.photo_url = photo_url
    await db.commit()
    await db.refresh(user)

    return {"photo_url": photo_url}


@router.post("/{user_id}/upload-document")
async def upload_document(
    user_id: int,
    file: UploadFile = File(...),
    doc_type: str = Form(...),   # e.g. "aadhar", "pan", "other"
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a document (PDF/image) for the given user. doc_type: aadhar | pan | other"""
    if current_user.id != user_id and current_user.role not in ("admin", "project_manager"):
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if file.content_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed. Use PDF or image.")

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "pdf"
    filename = f"{user_id}_{doc_type}_{uuid.uuid4().hex[:8]}.{ext}"
    save_path = os.path.join(DOCS_DIR, filename)

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc_url = f"/static/uploads/documents/{filename}"

    # Load existing documents list
    try:
        docs = json.loads(user.documents_url or "[]")
    except (json.JSONDecodeError, TypeError):
        docs = []

    # Replace existing doc of same type if present
    docs = [d for d in docs if d.get("doc_type") != doc_type]
    docs.append({
        "doc_type": doc_type,
        "url": doc_url,
        "filename": file.filename,
    })

    user.documents_url = json.dumps(docs)
    await db.commit()
    await db.refresh(user)

    return {"doc_type": doc_type, "url": doc_url, "filename": file.filename}


@router.get("/{user_id}/documents")
async def get_documents(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return list of uploaded documents for a user."""
    if current_user.id != user_id and current_user.role not in ("admin", "project_manager"):
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        docs = json.loads(user.documents_url or "[]")
    except (json.JSONDecodeError, TypeError):
        docs = []

    return docs


@router.delete("/{user_id}/documents/{doc_type}")
async def delete_document(
    user_id: int,
    doc_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a specific document from a user's profile."""
    if current_user.id != user_id and current_user.role not in ("admin", "project_manager"):
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        docs = json.loads(user.documents_url or "[]")
    except (json.JSONDecodeError, TypeError):
        docs = []

    to_delete = next((d for d in docs if d.get("doc_type") == doc_type), None)
    if to_delete:
        # Delete file from disk
        file_path = os.path.join(STATIC_DIR, *to_delete["url"].split("/static/", 1)[-1].split("/"))
        if os.path.exists(file_path):
            os.remove(file_path)
        docs = [d for d in docs if d.get("doc_type") != doc_type]
        user.documents_url = json.dumps(docs)
        await db.commit()

    return {"detail": f"Document '{doc_type}' removed."}