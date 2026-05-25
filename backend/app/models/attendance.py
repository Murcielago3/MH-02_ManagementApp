from sqlalchemy import Column, Integer, String, Date, Time, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(String, nullable=True)   # stored as HH:MM string
    check_out = Column(String, nullable=True)
    is_site_visit = Column(Boolean, default=False)
    site_name = Column(String, nullable=True)
    site_timing = Column(String, nullable=True)

    employee = relationship("User", foreign_keys=[employee_id])

    