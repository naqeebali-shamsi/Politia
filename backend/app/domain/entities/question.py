from dataclasses import dataclass
from datetime import date


@dataclass
class QuestionRecord:
    id: int | None = None
    politician_id: int = 0
    term_number: int | None = None
    question_date: date | None = None
    ministry: str | None = None
    question_type: str | None = None  # Starred / Unstarred
    question_title: str | None = None
    question_text: str | None = None
    answer_text: str | None = None
    source_url: str | None = None
