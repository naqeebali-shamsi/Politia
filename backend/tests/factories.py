"""
Factory functions for creating test domain entities with sensible defaults.
"""
from datetime import datetime, timezone

from app.domain.entities.politician import Politician
from app.domain.entities.score import ScoreRecord
from app.domain.entities.activity import ActivityRecord
from app.domain.entities.disclosure import DisclosureRecord
from app.domain.entities.election import ElectionRecord
from app.domain.entities.constituency import Constituency


def make_politician(
    id: int | None = None,
    full_name: str = "Narendra Modi",
    current_party: str = "BJP",
    current_state: str = "Gujarat",
    current_chamber: str = "Lok Sabha",
    current_constituency: str = "Varanasi",
    is_active: bool = True,
    **kwargs,
) -> Politician:
    return Politician(
        id=id, full_name=full_name, current_party=current_party,
        current_state=current_state, current_chamber=current_chamber,
        current_constituency=current_constituency, is_active=is_active,
        **kwargs,
    )


def make_score(
    id: int | None = None,
    politician_id: int = 1,
    overall_score: float = 75.0,
    participation_score: float = 70.0,
    disclosure_score: float = 80.0,
    integrity_risk_adjustment: float = 90.0,
    formula_version: str = "v1",
    is_current: bool = True,
    **kwargs,
) -> ScoreRecord:
    return ScoreRecord(
        id=id, politician_id=politician_id, overall_score=overall_score,
        participation_score=participation_score, disclosure_score=disclosure_score,
        integrity_risk_adjustment=integrity_risk_adjustment,
        formula_version=formula_version, is_current=is_current,
        computed_at=kwargs.pop("computed_at", datetime.now(timezone.utc)),
        **kwargs,
    )


def make_activity(
    id: int | None = None,
    politician_id: int = 1,
    term_number: int = 18,
    attendance_percentage: float = 85.0,
    questions_asked: int = 50,
    debates_participated: int = 20,
    private_bills_introduced: int = 2,
    committee_memberships: int = 3,
    **kwargs,
) -> ActivityRecord:
    return ActivityRecord(
        id=id, politician_id=politician_id, term_number=term_number,
        attendance_percentage=attendance_percentage, questions_asked=questions_asked,
        debates_participated=debates_participated,
        private_bills_introduced=private_bills_introduced,
        committee_memberships=committee_memberships,
        **kwargs,
    )


def make_disclosure(
    id: int | None = None,
    politician_id: int = 1,
    election_year: int = 2024,
    total_assets: float = 50_000_000.0,
    total_liabilities: float = 1_000_000.0,
    criminal_cases: int = 0,
    serious_criminal_cases: int = 0,
    affidavit_complete: bool = True,
    pan_declared: bool = True,
    **kwargs,
) -> DisclosureRecord:
    return DisclosureRecord(
        id=id, politician_id=politician_id, election_year=election_year,
        total_assets=total_assets, total_liabilities=total_liabilities,
        criminal_cases=criminal_cases, serious_criminal_cases=serious_criminal_cases,
        affidavit_complete=affidavit_complete, pan_declared=pan_declared,
        **kwargs,
    )


def make_election(
    id: int | None = None,
    politician_id: int = 1,
    constituency_id: int = 1,
    election_year: int = 2024,
    party: str = "BJP",
    result: str = "Won",
    votes: int = 500_000,
    vote_share: float = 55.0,
    margin: int = 100_000,
    **kwargs,
) -> ElectionRecord:
    return ElectionRecord(
        id=id, politician_id=politician_id, constituency_id=constituency_id,
        election_year=election_year, party=party, result=result,
        votes=votes, vote_share=vote_share, margin=margin,
        **kwargs,
    )


def make_constituency(
    id: int | None = None,
    name: str = "Varanasi",
    state: str = "Uttar Pradesh",
    chamber: str = "Lok Sabha",
    constituency_type: str = "General",
    **kwargs,
) -> Constituency:
    return Constituency(
        id=id, name=name, state=state, chamber=chamber,
        constituency_type=constituency_type, **kwargs,
    )
