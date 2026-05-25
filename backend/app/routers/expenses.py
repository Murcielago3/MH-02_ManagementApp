from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date
from pydantic import BaseModel
from app.database import get_db
from app.models.expense import Expense
from app.auth import require_admin, require_manager

router = APIRouter(prefix="/expenses", tags=["expenses"])

class ExpenseCreate(BaseModel):
    title: str
    category: str
    amount: float
    date: date  
    recurring: bool = False
    notes: Optional[str] = None

class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[date] = None
    recurring: Optional[bool] = None
    notes: Optional[str] = None

@router.get("/")
async def list_expenses(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    query = select(Expense)
    if category:
        query = query.where(Expense.category == category)
    result = await db.execute(query)
    expenses = result.scalars().all()
    return expenses

@router.post("/", status_code=201)
async def create_expense(
    data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    expense = Expense(
        title=data.title,
        category=data.category,
        amount=data.amount,
        date=data.date,
        recurring=data.recurring,
        notes=data.notes,
        added_by=current_user.id
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense

@router.patch("/{expense_id}")
async def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)
    await db.commit()
    await db.refresh(expense)
    return expense

@router.delete("/{expense_id}", status_code=204)
async def delete_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    await db.delete(expense)
    await db.commit()