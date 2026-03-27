from app.domain.interfaces.politician_repository import PoliticianRepository
from app.domain.interfaces.score_repository import ScoreRepository


class LeaderboardService:
    def __init__(
        self,
        politician_repo: PoliticianRepository,
        score_repo: ScoreRepository,
    ):
        self._politicians = politician_repo
        self._scores = score_repo

    def get_leaderboard(
        self,
        chamber: str | None = None,
        state: str | None = None,
        party: str | None = None,
        sort_by: str = "overall_score",
        offset: int = 0,
        limit: int = 20,
    ) -> dict:
        allowed_sort = {
            "overall_score", "participation_score", "disclosure_score",
            "integrity_risk_adjustment",
        }
        if sort_by not in allowed_sort:
            sort_by = "overall_score"

        total = self._scores.count_leaderboard(
            chamber=chamber, state=state, party=party,
        )

        entries = self._scores.get_leaderboard(
            chamber=chamber, state=state, party=party,
            sort_by=sort_by, offset=offset, limit=limit,
        )

        # Single bulk fetch instead of N+1
        pol_ids = [pid for pid, _ in entries]
        politicians = self._politicians.get_by_ids(pol_ids) if pol_ids else {}

        results = []
        for rank, (pid, score) in enumerate(entries, start=offset + 1):
            p = politicians.get(pid)
            if not p:
                continue
            results.append({
                "rank": rank,
                "id": p.id,
                "full_name": p.full_name,
                "party": p.current_party,
                "state": p.current_state,
                "chamber": p.current_chamber,
                "constituency": p.current_constituency,
                "photo_url": p.photo_url,
                "score": score.overall_score,
                "participation_score": score.participation_score,
                "disclosure_score": score.disclosure_score,
                "integrity_risk_adjustment": score.integrity_risk_adjustment,
            })

        return {"results": results, "total": total, "offset": offset, "limit": limit}
