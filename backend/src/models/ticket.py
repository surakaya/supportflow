from sqlalchemy import Column, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from src.core.database import Base


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("company_id", "idempotency_key", name="uq_ticket_idempotency"),
    )

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=False, index=True)
    message = Column(Text, nullable=False)
    idempotency_key = Column(String(64), nullable=False, index=True)
    category = Column(String(64), nullable=True)
    urgency = Column(String(64), nullable=True)
    priority = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
