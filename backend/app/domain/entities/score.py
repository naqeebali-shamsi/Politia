from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScoreRecord:
    id: int | None = None
    politician_id: int = 0
    overall_score: float = 0.0
    participation_score: float = 0.0
    disclosure_score: float = 0.0
    integrity_risk_adjustment: float = 0.0

    # Component breakdowns (stored as JSON for flexibility)
    participation_breakdown: dict | None = None
    disclosure_breakdown: dict | None = None
    integrity_breakdown: dict | None = None

    formula_version: str = "v1"
    computed_at: datetime | None = None
    is_current: bool = True  # Only one current score per politician
