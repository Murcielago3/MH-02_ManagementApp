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
    pan_number = Column(String, nullable=True)
    aadhar_number = Column(String, nullable=True)
    personal_mail = Column(String, nullable=False, unique=True)
    studio_email = Column(String, nullable=False, unique=True)
    photo_url = Column(String, nullable=True)
    documents_url = Column(String, nullable=True)
    time_tracker_login = Column(String, nullable=True)
    time_tracker_password = Column(String, nullable=True)
    role = Column(String, default="employee")
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String, nullable=False)
    documents_url = Column(String, nullable=True)

    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    manager = relationship("User", remote_side=[id])
    assignments = relationship("ProjectAssignment", back_populates="user")
