from pydantic import BaseModel
from datetime import datetime


class ScoreResponse(BaseModel):
    overall: float | None = None
    participation: float | None = None
    disclosure: float | None = None
    integrity_risk: float | None = None
    participation_breakdown: dict | None = None
    disclosure_breakdown: dict | None = None
    integrity_breakdown: dict | None = None
    formula_version: str | None = None
    computed_at: datetime | None = None


class PoliticianSummary(BaseModel):
    id: int
    full_name: str
    party: str | None = None
    state: str | None = None
    chamber: str | None = None
    constituency: str | None = None
    photo_url: str | None = None
    is_active: bool = True
    score: float | None = None


class ActivityResponse(BaseModel):
    term_number: int | None = None
    session_name: str | None = None
    attendance_percentage: float | None = None
    questions_asked: int | None = None
    debates_participated: int | None = None
    private_bills_introduced: int | None = None
    committee_memberships: int | None = None
    committee_names: list[str] | None = None


class DisclosureResponse(BaseModel):
    election_year: int
    total_assets: float | None = None
    movable_assets: float | None = None
    immovable_assets: float | None = None
    total_liabilities: float | None = None
    criminal_cases: int | None = None
    serious_criminal_cases: int | None = None
    affidavit_complete: bool | None = None


class ElectionResponse(BaseModel):
    election_year: int
    party: str
    result: str
    constituency_id: int | None = None
    votes: int | None = None
    vote_share: float | None = None
    margin: int | None = None


class PoliticianProfile(BaseModel):
    id: int
    full_name: str
    party: str | None = None
    state: str | None = None
    chamber: str | None = None
    constituency: str | None = None
    photo_url: str | None = None
    gender: str | None = None
    education: str | None = None
    profession: str | None = None
    is_active: bool = True
    last_updated: datetime | None = None
    scores: ScoreResponse | None = None
    activities: list[ActivityResponse] = []
    disclosures: list[DisclosureResponse] = []
    elections: list[ElectionResponse] = []


class SearchResponse(BaseModel):
    results: list[PoliticianSummary]
    total: int
    offset: int = 0
    limit: int = 20


class FiltersResponse(BaseModel):
    states: list[str]
    parties: list[str]
