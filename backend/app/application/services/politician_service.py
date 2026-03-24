from app.domain.interfaces.politician_repository import PoliticianRepository
from app.domain.interfaces.score_repository import ScoreRepository
from app.domain.interfaces.activity_repository import ActivityRepository
from app.domain.interfaces.disclosure_repository import DisclosureRepository
from app.domain.interfaces.election_repository import ElectionRepository


class PoliticianService:
    def __init__(
        self,
        politician_repo: PoliticianRepository,
        score_repo: ScoreRepository,
        activity_repo: ActivityRepository,
        disclosure_repo: DisclosureRepository,
        election_repo: ElectionRepository,
    ):
        self._politicians = politician_repo
        self._scores = score_repo
        self._activities = activity_repo
        self._disclosures = disclosure_repo
        self._elections = election_repo

    def search(
        self,
        query: str = "",
        state: str | None = None,
        party: str | None = None,
        chamber: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict:
        politicians = self._politicians.search(
            query=query, state=state, party=party,
            chamber=chamber, is_active=is_active,
            offset=offset, limit=limit,
        )
        total = self._politicians.search_count(
            query=query, state=state, party=party,
            chamber=chamber, is_active=is_active,
        )

        # Batch fetch scores for all results
        pol_ids = [p.id for p in politicians if p.id]
        scores = self._scores.get_scores_for_politicians(pol_ids) if pol_ids else {}

        results = []
        for p in politicians:
            score = scores.get(p.id)
            results.append({
                "id": p.id,
                "full_name": p.full_name,
                "party": p.current_party,
                "state": p.current_state,
                "chamber": p.current_chamber,
                "constituency": p.current_constituency,
                "photo_url": p.photo_url,
                "is_active": p.is_active,
                "score": score.overall_score if score else None,
            })

        return {"results": results, "total": total, "offset": offset, "limit": limit}

    def get_profile(self, politician_id: int) -> dict | None:
        politician = self._politicians.get_by_id(politician_id)
        if not politician:
            return None

        score = self._scores.get_current_score(politician_id)
        activities = self._activities.get_by_politician(politician_id)
        disclosures = self._disclosures.get_by_politician(politician_id)
        elections = self._elections.get_by_politician(politician_id)

        return {
            "politician": politician,
            "score": score,
            "activities": activities,
            "disclosures": disclosures,
            "elections": elections,
        }

    def get_filters(self) -> dict:
        return {
            "states": self._politicians.get_distinct_states(),
            "parties": self._politicians.get_distinct_parties(),
        }
