from datetime import date
from pydantic import BaseModel


class QuestionItem(BaseModel):
    id: int
    politician_id: int
    term_number: int | None = None
    question_date: date | None = None
    ministry: str | None = None
    question_type: str | None = None
    question_title: str | None = None
    source_url: str | None = None


class QuestionSearchResponse(BaseModel):
    results: list[QuestionItem]
    total: int
    offset: int = 0
    limit: int = 20


class MinistryStatItem(BaseModel):
    ministry: str
    count: int


class TermStatItem(BaseModel):
    term_number: int
    count: int


class QuestionStatsResponse(BaseModel):
    by_ministry: list[MinistryStatItem]
    by_term: list[TermStatItem]
    total: int
    ministries: list[str]
