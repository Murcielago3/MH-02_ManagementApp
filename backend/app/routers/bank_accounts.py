from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.bank_account import BankAccount
from app.auth import require_admin

router = APIRouter(prefix="/bank-accounts", tags=["bank-accounts"])

class BankAccountCreate(BaseModel):
    bank_name: str
    account_number: str
    account_type: str
    account_holder_name: str
    ifsc_code: str

class BankAccountUpdate(BaseModel):
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_type: Optional[str] = None
    account_holder_name: Optional[str] = None
    ifsc_code: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("/")
async def list_bank_accounts(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    # Bank accounts change rarely; safe to let the browser hold this for 30s.
    response.headers["Cache-Control"] = "private, max-age=30"
    result = await db.execute(
        select(BankAccount).where(BankAccount.is_active == True)
    )
    return result.scalars().all()

@router.post("/", status_code=201)
async def create_bank_account(
    data: BankAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    account = BankAccount(**data.model_dump())
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account

@router.patch("/{account_id}")
async def update_bank_account(
    account_id: int,
    data: BankAccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    result = await db.execute(
        select(BankAccount).where(BankAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(404, "Bank account not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    await db.commit()
    await db.refresh(account)
    return account

@router.delete("/{account_id}", status_code=204)
async def delete_bank_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    result = await db.execute(
        select(BankAccount).where(BankAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(404, "Bank account not found")
    account.is_active = False
    await db.commit()