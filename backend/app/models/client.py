from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class Client(Base):
    __tablename__="clients"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=False)
    gstin = Column(String, nullable=True)

    # 'business' or 'individual'. Individual clients show only PAN on invoices
    # (no GSTIN); business clients may carry both.
    customer_type = Column(String, nullable=False, default="business")
    pan = Column(String, nullable=True)

    # Alternate display name printed on invoices instead of `name`.
    # NULL = "same as client name" (falls back to `name` wherever it's read).
    salutation = Column(String, nullable=True)

    # Structured address. `address` (above) is kept for backward compatibility —
    # existing clients that predate these fields keep working — but new/edited
    # clients populate both, with `address` auto-derived from these on save.
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    pincode = Column(String, nullable=True)

    projects = relationship("Project", back_populates="client")
