from dataclasses import dataclass
from datetime import datetime


@dataclass
class Office:
    id: int | None = None
    politician_id: int = 0
    constituency_id: int | None = None
    title: str = "MP"
    chamber: str = ""
    party: str = ""
    term_number: int | None = None  # e.g. 17th Lok Sabha
    term_start: datetime | None = None
    term_end: datetime | None = None
    is_active: bool = True
