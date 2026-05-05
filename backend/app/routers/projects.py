from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.project import Project, ProjectAssignment
from app.models.user import User
from app.auth import require_admin, require_manager

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    project_number: str
    name: str
    location: Optional[str] = None
    gmap_link: Optional[str] = None
    year: Optional[int] = None
    current_stage: Optional[str] = None
    is_billed: str = "unbilled"
    client_id: Optional[int] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    gmap_link: Optional[str] = None
    year: Optional[int] = None
    current_stage: Optional[str] = None
    is_billed: Optional[str] = None
    client_id: Optional[int] = None

@router.get("/")
async def list_projects(
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    query = select(Project)
    if year:
        query = query.where(Project.year == year)
    result = await db.execute(query)
    projects = result.scalars().all()
    return projects 

@router.get("/{project_id}")
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/", status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    project = Project(
        project_number=data.project_number,
        name=data.name,
        location=data.location,
        gmap_link=data.gmap_link,
        year=data.year,
        current_stage=data.current_stage,
        is_billed=data.is_billed,
        client_id=data.client_id
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

@router.patch("/{project_id}")
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for field, value in data.dict(exclude_unset=True).items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    return project

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
    return {"detail": "Project deleted successfully"}

class AssignUserBody(BaseModel):
    user_id: int

@router.post("/{project_id}/assign", status_code=201)
async def assign_user_to_project(
    project_id: int,
    data: AssignUserBody,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    assignment = ProjectAssignment(project_id=project_id, user_id=data.user_id)
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment