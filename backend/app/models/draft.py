from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Draft(Base):
    """A per-user, account-synced draft.

    Replaces the old browser-localStorage drafts so a user's in-progress work
    (estimates, invoices, half-filled create forms, timesheets) follows their
    account across devices instead of being trapped on one browser.

    Identified by (user_id, namespace, draft_key):
      • namespace groups drafts by feature, e.g. "estimate", "invoice",
        "client_create", "timesheet_2026-05-26".
      • draft_key distinguishes multiple drafts within a namespace. Feature areas
        that keep a list of drafts (estimates, invoices) generate a unique key
        per draft; single-slot autosave forms use a fixed key ("default").
    """

    __tablename__ = "drafts"
    __table_args__ = (
        UniqueConstraint("user_id", "namespace", "draft_key", name="uq_draft_user_ns_key"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    namespace = Column(String, nullable=False, index=True)
    draft_key = Column(String, nullable=False)
    label = Column(String, nullable=True)
    data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
