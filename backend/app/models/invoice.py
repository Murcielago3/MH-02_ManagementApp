from sqlalchemy import Column, Integer, Numeric, String, Float, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import date

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    invoice_type = Column(String, nullable=False)  # tax, proforma
    invoice_number = Column(String, nullable=True)  # only for tax
    invoice_date = Column(Date, default=date.today)
    place_of_supply = Column(String, nullable=True)

    bill_to_name = Column(String, nullable=True)
    bill_to_address = Column(String, nullable=True)
    bill_to_gstin = Column(String, nullable=True)

    ship_to_name = Column(String, nullable=True)
    ship_to_address = Column(String, nullable=True)
    ship_to_gstin = Column(String, nullable=True)

    subject = Column(String, nullable=True)

    subtotal = Column(Numeric(12, 2), default=0)
    cgst = Column(Numeric(12, 2), default=0)
    sgst = Column(Numeric(12, 2), default=0)
    igst = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), default=0)
    tax_type = Column(String, nullable=True)  # CGST_SGST or IGST

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    bank_account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    project = relationship("Project", foreign_keys=[project_id])
    client = relationship("Client", foreign_keys=[client_id])
    bank_account = relationship("BankAccount", foreign_keys=[bank_account_id])
    items = relationship("InvoiceItem", back_populates="invoice",
                        cascade="all, delete-orphan")
    
class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(String, nullable=False)
    hsn_sac = Column(String, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="items")