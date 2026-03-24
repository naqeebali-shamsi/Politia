from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    total: int | None = None
    offset: int = 0
    limit: int = 20


class ErrorResponse(BaseModel):
    detail: str
