from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import enforce_rate_limit, get_current_company
from src.models.company import Company
from src.schemas.ticket import AnalyzeRequest, AnalyzeResponse
from src.services.ticket_service import create_ticket

router = APIRouter()


@router.post("/", response_model=AnalyzeResponse)
def analyze_ticket(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
    _: None = Depends(enforce_rate_limit),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    key = idempotency_key or payload.idempotency_key
    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header (or idempotency_key field) is required",
        )

    try:
        ticket = create_ticket(db, company_id=company.id, payload=payload, idempotency_key=key)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return ticket
