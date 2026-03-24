from dataclasses import dataclass


@dataclass
class ActivityRecord:
    id: int | None = None
    politician_id: int = 0
    term_number: int | None = None  # e.g. 18 for 18th Lok Sabha
    session_name: str | None = None  # e.g. "Budget Session 2024"
    attendance_percentage: float | None = None
    questions_asked: int = 0
    debates_participated: int = 0
    private_bills_introduced: int = 0
    committee_memberships: int = 0
    committee_names: list[str] | None = None
    source_id: int | None = None
