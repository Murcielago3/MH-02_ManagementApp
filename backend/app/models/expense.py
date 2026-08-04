from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    # `amount` is the bill total (base + GST). Kept as the headline figure so the
    # monthly report and dashboards that sum it stay correct.
    amount = Column(Numeric(12, 2), nullable=False)
    base_amount = Column(Numeric(12, 2), nullable=True)   # pre-GST
    gst_percent = Column(Numeric(5, 2), nullable=True, default=0)
    gst_amount = Column(Numeric(12, 2), nullable=True, default=0)
    party_id = Column(Integer, ForeignKey("expense_parties.id", ondelete="SET NULL"), nullable=True)
    date = Column(Date, nullable=False)
    recurring = Column(Boolean, default=False)
    notes = Column(String, nullable=True)

    party = relationship("ExpenseParty", foreign_keys=[party_id])

    added_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    added_by_user = relationship("User")

    