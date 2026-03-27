from fastapi import APIRouter, Depends, Query

from app.dependencies import get_leaderboard_service
from app.application.services.leaderboard_service import LeaderboardService
from app.api.schemas.leaderboard import LeaderboardResponse, LeaderboardEntry

router = APIRouter(prefix="/leaderboards", tags=["Leaderboards"])


@router.get("", response_model=LeaderboardResponse)
def get_leaderboard(
    chamber: str | None = None,
    state: str | None = None,
    party: str | None = None,
    sort_by: str = "overall_score",
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: LeaderboardService = Depends(get_leaderboard_service),
):
    result = service.get_leaderboard(
        chamber=chamber, state=state, party=party,
        sort_by=sort_by, offset=offset, limit=limit,
    )
    return LeaderboardResponse(
        results=[LeaderboardEntry(**r) for r in result["results"]],
        total=result["total"],
        offset=result["offset"],
        limit=result["limit"],
    )
