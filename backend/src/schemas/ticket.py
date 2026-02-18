from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    message: str | None = None
    idempotency_key: str | None = None


class AnalyzeResponse(BaseModel):
    status: str
    ticket_id: int
