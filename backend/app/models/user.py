from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    designation = Column(String, nullable=False)
    joining_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    salary_month = Column(Numeric(10, 2))
    salary_hour = Column(Numeric(8, 2), nullable=True)
    leaves_allowed = Column(Integer, default=12)
    # Running paid-leave balance (supports half-days); accrues 1.5/month.
    paid_leave_balance = Column(Numeric(6, 1), default=0)
    # Last month (YYYY-MM) the monthly accrual was applied — for idempotent accrual.
    leave_accrued_through = Column(String, nullable=True)
    pan_number = Column(String, nullable=True)
    aadhar_number = Column(String, nullable=True)
    gender = Column(String, nullable=True)            # e.g. "M" / "F" / "Other"
    location = Column(String, nullable=True)          # work location, shown on salary slip
    bank_name = Column(String, nullable=True)         # employee's bank, shown on salary slip
    bank_account_number = Column(String, nullable=True)
    bank_ifsc_code = Column(String, nullable=True)
    birthdate = Column(Date, nullable=True)
    personal_mail = Column(String, nullable=False, unique=True)
    studio_email = Column(String, nullable=False, unique=True)
    photo_url = Column(String, nullable=True)
    documents_url = Column(String, nullable=True)
    time_tracker_login = Column(String, nullable=True)
    time_tracker_password = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_number = Column(String, nullable=True)
    emergency_contact_relationship = Column(String, nullable=True)
    role = Column(String, default="employee")
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String, nullable=False)
    documents_url = Column(String, nullable=True)

    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    manager = relationship("User", remote_side=[id])
    assignments = relationship("ProjectAssignment", back_populates="user")
    # weekly_timesheets now has multiple FKs to users (employee_id + the
    # pm/admin/rejected approval slots) — the join must be pinned to employee_id
    # or the User mapper fails to configure (which 500s every request).
    weekly_timesheets = relationship(
        "WeeklyTimesheet", back_populates="employee",
        foreign_keys="WeeklyTimesheet.employee_id",
    )
