from pydantic import BaseModel
from typing import Any


class AnomalyItem(BaseModel):
    full_name: str
    party: str | None = None
    state: str | None = None
    election_year: int | None = None
    total_assets: float | None = None
    anomaly_type: str | None = None
    detail: str | None = None
    severity: str | None = None
    total_assets_fmt: str | None = None


class AnomaliesResponse(BaseModel):
    anomalies: list[AnomalyItem]
    total: int
    offset: int = 0
    limit: int = 50


class PartyTrendItem(BaseModel):
    election_year: int | None = None
    party: str | None = None
    candidates: int | None = None
    seats_won: int | None = None
    total_votes: float | None = None
    avg_vote_share: float | None = None
    win_rate: float | None = None


class PartyTrendsResponse(BaseModel):
    trends: list[PartyTrendItem]
    total: int


class CrorepatiTrendItem(BaseModel):
    election_year: int | None = None
    total_candidates: int | None = None
    crorepati_count: int | None = None
    crorepati_pct: float | None = None
    avg_assets: float | None = None
    median_assets: float | None = None
    avg_liabilities: float | None = None
    avg_movable: float | None = None
    avg_immovable: float | None = None


class CrorepatiTrendsResponse(BaseModel):
    trends: list[CrorepatiTrendItem]
    total: int
