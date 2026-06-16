"""Singleton row holding admin-configurable app settings.

Currently:
  - Company profile (used in invoice PDFs)
  - Compensation defaults (used by the hourly-rate formula in projects)
"""
from sqlalchemy import Column, Integer, String, Numeric
from app.database import Base


class Settings(Base):
    __tablename__ = "settings"

    # Always row id = 1; we treat this as a singleton
    id = Column(Integer, primary_key=True)

    # ─── Company profile (invoice PDF) ───
    company_name = Column(String, nullable=True)
    company_address = Column(String, nullable=True)
    company_gstin = Column(String, nullable=True)
    company_phone = Column(String, nullable=True)
    company_email = Column(String, nullable=True)
    company_signatory_name = Column(String, nullable=True)
    company_signatory_role = Column(String, nullable=True)

    # ─── Compensation defaults (hourly rate formula) ───
    # hourly_rate = (salary_month * salary_months_per_year / 12) / working_hours_per_month
    working_hours_per_month = Column(Numeric(6, 2), nullable=True)   # default 160
    salary_months_per_year = Column(Numeric(4, 2), nullable=True)    # default 13

    # ─── Payroll ───
    tds_percent = Column(Numeric(5, 2), nullable=True)   # TDS % deducted from base salary; default 10
