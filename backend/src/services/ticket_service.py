from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.ticket import Ticket
from src.schemas.ticket import AnalyzeRequest, AnalyzeResponse
from src.services.ml_service import analyze_text
from src.services.priority_service import calculate_priority, normalize_urgency


def create_ticket(
    db: Session,
    company_id: int,
    payload: AnalyzeRequest,
    idempotency_key: str,
) -> AnalyzeResponse:
    existing = (
        db.query(Ticket)
        .filter(
            Ticket.company_id == company_id,
            Ticket.idempotency_key == idempotency_key,
        )
        .first()
    )
    if existing:
        return AnalyzeResponse(status="processed", ticket_id=existing.id)

    message = (payload.message or "").strip()
    if not message:
        parts = [payload.title or "", payload.description or ""]
        message = "\n".join(part for part in parts if part).strip()

    if not message:
        raise ValueError("message is required")

    result = analyze_text(message)
    urgency = normalize_urgency(result.get("urgency"))
    priority = calculate_priority(
        category=result.get("category"),
        urgency=urgency,
        confidence=result.get("confidence"),
        ml_priority=result.get("priority"),
    )

    ticket = Ticket(
        company_id=company_id,
        message=message,
        idempotency_key=idempotency_key,
        category=result.get("category"),
        urgency=urgency,
        priority=priority,
        confidence=result.get("confidence"),
    )

    db.add(ticket)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(Ticket)
            .filter(
                Ticket.company_id == company_id,
                Ticket.idempotency_key == idempotency_key,
            )
            .first()
        )
        if existing:
            return AnalyzeResponse(status="processed", ticket_id=existing.id)
        raise

    db.refresh(ticket)
    return AnalyzeResponse(status="processed", ticket_id=ticket.id)
