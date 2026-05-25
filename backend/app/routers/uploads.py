from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import uuid
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.auth import get_current_user, require_manager, require_admin

router = APIRouter(prefix="/uploads", tags=["uploads"])

UPLOAD_DIR = "static/uploads"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif"}
ALLOWED_DOCUMENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}

def save_file(file: UploadFile, subfolder: str) -> str:
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, subfolder, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as buffer:
        buffer.write(file.file.read())
    return f"/static/uploads/{subfolder}/{filename}"

@router.post("/employee/{user_id}/photo")
async def upload_employee_photo(
    user_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "Only JPEG, PNG, or WebP images allowed")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    url = save_file(file, "photos")
    user.photo_url = url
    await db.commit()
    return {"photo_url": url}

@router.post("/employee/{user_id}/document")
async def upload_employee_document(
    user_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if file.content_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(400, "Only PDF, JPEG, or PNG files allowed")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    
    url = save_file(file, "documents")
    # Here you would typically save the document URL to the database, associated with the user
    user.documents_url = url  # Assuming you have a field for this
    await db.commit()
    return {"document_url": url}

@router.post("/project/{project_id}/workorder")
async def upload_project_workorder(
    project_id: int, 
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    if file.content_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(400, "Only PDF, JPEG, or PNG files allowed")
    
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    
    url = save_file(file, "documents")
    if not project.workorder_url:
        project.workorder_url = url
    else:
        project.work_order_url += f";{url}"  # If you want to support multiple work orders, separate URLs with a semicolon
    # Here you would typically save the work order URL to the database, associated with the project
    project.workorder_url = url  # Assuming you have a field for this
    await db.commit()
    return {"workorder_url": url}

