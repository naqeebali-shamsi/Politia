from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    id: int
    full_name: str
    party: str | None = None
    state: str | None = None
    chamber: str | None = None
    constituency: str | None = None
    photo_url: str | None = None
    score: float
    participation_score: float | None = None
    disclosure_score: float | None = None
    integrity_risk_adjustment: float | None = None


class LeaderboardResponse(BaseModel):
    results: list[LeaderboardEntry]
    offset: int = 0
    limit: int = 20
