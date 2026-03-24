from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_politician_service
from app.application.services.politician_service import PoliticianService
from app.api.schemas.politician import (
    SearchResponse, PoliticianProfile, PoliticianSummary,
    ScoreResponse, ActivityResponse, DisclosureResponse,
    ElectionResponse, FiltersResponse,
)
from app.config import get_settings

router = APIRouter(prefix="/politicians", tags=["Politicians"])


@router.get("", response_model=SearchResponse)
def search_politicians(
    q: str = "",
    state: str | None = None,
    party: str | None = None,
    chamber: str | None = None,
    is_active: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: PoliticianService = Depends(get_politician_service),
):
    result = service.search(
        query=q, state=state, party=party,
        chamber=chamber, is_active=is_active,
        offset=offset, limit=limit,
    )
    return SearchResponse(
        results=[PoliticianSummary(**r) for r in result["results"]],
        total=result["total"],
        offset=result["offset"],
        limit=result["limit"],
    )


@router.get("/filters", response_model=FiltersResponse)
def get_filters(
    service: PoliticianService = Depends(get_politician_service),
):
    return service.get_filters()


@router.get("/{politician_id}", response_model=PoliticianProfile)
def get_politician_profile(
    politician_id: int,
    service: PoliticianService = Depends(get_politician_service),
):
    profile = service.get_profile(politician_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Politician not found")

    p = profile["politician"]
    score = profile["score"]

    return PoliticianProfile(
        id=p.id,
        full_name=p.full_name,
        party=p.current_party,
        state=p.current_state,
        chamber=p.current_chamber,
        constituency=p.current_constituency,
        photo_url=p.photo_url,
        gender=p.gender,
        education=p.education,
        profession=p.profession,
        is_active=p.is_active,
        last_updated=p.last_updated,
        scores=ScoreResponse(
            overall=score.overall_score,
            participation=score.participation_score,
            disclosure=score.disclosure_score,
            integrity_risk=score.integrity_risk_adjustment,
            participation_breakdown=score.participation_breakdown,
            disclosure_breakdown=score.disclosure_breakdown,
            integrity_breakdown=score.integrity_breakdown,
            formula_version=score.formula_version,
            computed_at=score.computed_at,
        ) if score else None,
        activities=[
            ActivityResponse(
                term_number=a.term_number,
                session_name=a.session_name,
                attendance_percentage=a.attendance_percentage,
                questions_asked=a.questions_asked,
                debates_participated=a.debates_participated,
                private_bills_introduced=a.private_bills_introduced,
                committee_memberships=a.committee_memberships,
                committee_names=a.committee_names,
            ) for a in profile["activities"]
        ],
        disclosures=[
            DisclosureResponse(
                election_year=d.election_year,
                total_assets=d.total_assets,
                movable_assets=d.movable_assets,
                immovable_assets=d.immovable_assets,
                total_liabilities=d.total_liabilities,
                criminal_cases=d.criminal_cases,
                serious_criminal_cases=d.serious_criminal_cases,
                affidavit_complete=d.affidavit_complete,
            ) for d in profile["disclosures"]
        ],
        elections=[
            ElectionResponse(
                election_year=e.election_year,
                party=e.party,
                result=e.result,
                constituency_id=e.constituency_id,
                votes=e.votes,
                vote_share=e.vote_share,
                margin=e.margin,
            ) for e in profile["elections"]
        ],
    )
