from sqlalchemy import Column, Integer, String, Date
from app.database import Base


class Holiday(Base):
    """A public / company-wide non-working day that applies to every employee.

    Surfaced (greyed out) across the task calendar and employee dashboards,
    treated the same way weekends are.
    """
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, unique=True)
    name = Column(String, nullable=False)
