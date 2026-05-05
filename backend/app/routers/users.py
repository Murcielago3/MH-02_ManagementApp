from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.auth import get_current_user, require_admin, require_manager, hash_password

router = APIRouter(prefix="/users", tags=["users"])

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
    leaves_allowed: int = 18
    pan_number: str
    aadhar_number: str
    manager_id: Optional[int] = None

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
    leaves_allowed: Optional[int] = None
    pan_number: Optional[str] = None
    aadhar_number: Optional[str] = None
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None

#----ROUTES----

@router.get("/")
async def list_users(
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.is_active == True))
    users = result.scalars().all()
    return users

@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.get("/{user_id}")
async def get_user(
    user_id: int,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db)
):
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
        leaves_allowed=data.leaves_allowed,
        pan_number=data.pan_number,
        aadhar_number=data.aadhar_number,
        manager_id=data.manager_id
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
    current_user: User = Depends(require_manager)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
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