from fastapi import APIRouter, Depends
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
    return db.query(Ticket).filter(Ticket.company_id == company.id).all()
