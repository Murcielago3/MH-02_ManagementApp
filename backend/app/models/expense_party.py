"""Expense parties (vendors) and expense payments.

A party is a reusable vendor whose basic details prefill an expense so bills
from the same supplier are quick to record. An expense can be paid in parts, so
it has many ExpensePayments - the money-out mirror of InvoicePayment.
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ExpenseParty(Base):
    __tablename__ = "expense_parties"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    gstin = Column(String, nullable=True)
    pan = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    # Prefills the GST% when this party is picked on an expense.
    default_gst_percent = Column(Numeric(5, 2), nullable=True, default=18)
    notes = Column(String, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class ExpensePayment(Base):
    __tablename__ = "expense_payments"

    id = Column(Integer, primary_key=True)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False, default=0)
    payment_date = Column(Date, nullable=False)
    note = Column(String, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    expense = relationship("Expense", backref="payments")
