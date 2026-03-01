from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import get_current_company
from src.models.company import Company
from src.models.ticket import Ticket

router = APIRouter()


@router.get("/")
def list_tickets(
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    return (
        db.query(Ticket)
        .filter(Ticket.company_id == company.id)
        .order_by(Ticket.id.desc())
        .all()
    )


@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    ticket = (
        db.query(Ticket)
        .filter(
            Ticket.id == ticket_id,
            Ticket.company_id == company.id,
        )
        .first()
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    return ticket
