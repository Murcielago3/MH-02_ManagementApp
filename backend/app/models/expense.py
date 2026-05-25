from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    date = Column(Date, nullable=False)
    recurring = Column(Boolean, default=False)
    notes = Column(String, nullable=True)

    added_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    added_by_user = relationship("User")

    