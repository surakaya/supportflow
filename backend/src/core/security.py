from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.company import Company
from src.utils.rate_limit import rate_limiter


def get_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is required",
        )
    return x_api_key


def enforce_rate_limit(api_key: str = Depends(get_api_key)) -> None:
    allowed, retry_after = rate_limiter.check(api_key)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )


def get_current_company(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
) -> Company:
    company = db.query(Company).filter(Company.api_key == api_key).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return company
