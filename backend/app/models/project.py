from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    project_number = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    gmap_link = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    current_stage = Column(String, nullable=True)
    is_billed = Column(String, default="unbilled")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    client = relationship("Client", back_populates="projects")
    assignments = relationship("ProjectAssignment", back_populates="project", cascade="all, delete-orphan")
    work_order_urls = Column(String, nullable=True)  # comma-separated URLs

    color = Column(String, nullable=True, default='#287475')

    partner_remuneration = Column(Numeric(10, 2), nullable=True, default=0)
    employee_remuneration = Column(Numeric(10, 2), nullable=True, default=0)
    project_remuneration = Column(Numeric(10, 2), nullable=True, default=0)
    total_assigned_hours = Column(Numeric(10, 2), nullable=True, default=0)
    partner_hourly_rate = Column(Numeric(10, 2), nullable=True, default=0)
    employee_budget = Column(Numeric(12, 2), nullable=True, default=0)
    partner_budget = Column(Numeric(12, 2), nullable=True, default=0)
    billed_amount = Column(Numeric(12, 2), nullable=True, default=0)
    advance_amount = Column(Numeric(12, 2), nullable=True, default=0)



class ProjectAssignment(Base):
    __tablename__ = "project_assignments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    base_pay = Column(Numeric(10, 2), nullable=True)
    hourly_rate = Column(Numeric(8, 2), nullable=True)

    user = relationship("User", back_populates="assignments")
    project = relationship("Project", back_populates="assignments")


