"""Payments received against an invoice.

An invoice can be settled in parts, so it has many payments. For each payment
the user records the amount that actually reached the bank; if TDS was cut, the
gross settled amount is grossed up from it, because TDS is the client's money
withheld for the government, not a shortfall:

    settled = received / (1 - tds_percent/100)    (when TDS cut)
    tds     = settled - received

The invoice is "paid" once the sum of settled amounts reaches its total.
Money-in mirror of ExpensePayment (money-out).
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class InvoicePayment(Base):
    __tablename__ = "invoice_payments"

    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)

    # What actually hit the bank.
    received_amount = Column(Numeric(12, 2), nullable=False, default=0)
    # TDS slab cut by the client: 0 (none), 2 (194C) or 10 (194J).
    tds_percent = Column(Numeric(5, 2), nullable=False, default=0)
    tds_amount = Column(Numeric(12, 2), nullable=False, default=0)
    # received + tds — the amount this payment settles against the invoice total.
    settled_amount = Column(Numeric(12, 2), nullable=False, default=0)

    payment_date = Column(Date, nullable=False)
    note = Column(String, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    invoice = relationship("Invoice", backref="payments")
