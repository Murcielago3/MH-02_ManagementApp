from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True)
    bank_name = Column(String, nullable=False)
    account_number = Column(String, nullable=False)
    account_type = Column(String, nullable=False)  # Current, Savings
    account_holder_name = Column(String, nullable=False)
    ifsc_code = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)