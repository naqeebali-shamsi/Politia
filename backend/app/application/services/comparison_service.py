from app.domain.interfaces.politician_repository import PoliticianRepository
from app.domain.interfaces.score_repository import ScoreRepository
from app.domain.interfaces.activity_repository import ActivityRepository
from app.domain.interfaces.disclosure_repository import DisclosureRepository


class ComparisonService:
    MAX_COMPARE = 5

    def __init__(
        self,
        politician_repo: PoliticianRepository,
        score_repo: ScoreRepository,
        activity_repo: ActivityRepository,
        disclosure_repo: DisclosureRepository,
    ):
        self._politicians = politician_repo
        self._scores = score_repo
        self._activities = activity_repo
        self._disclosures = disclosure_repo

    def compare(self, politician_ids: list[int]) -> dict:
        if len(politician_ids) < 2:
            raise ValueError("Need at least 2 politicians to compare")
        if len(politician_ids) > self.MAX_COMPARE:
            raise ValueError(f"Cannot compare more than {self.MAX_COMPARE} politicians")

        scores = self._scores.get_scores_for_politicians(politician_ids)

        comparisons = []
        for pid in politician_ids:
            politician = self._politicians.get_by_id(pid)
            if not politician:
                continue

            score = scores.get(pid)
            activities = self._activities.get_by_politician(pid)
            disclosure = self._disclosures.get_latest_by_politician(pid)

            # Aggregate activity stats
            total_questions = sum(a.questions_asked for a in activities)
            total_debates = sum(a.debates_participated for a in activities)
            with_attendance = [a for a in activities if a.attendance_percentage is not None]
            avg_attendance = (
                sum(a.attendance_percentage for a in with_attendance) / len(with_attendance)
                if with_attendance else None
            )

            comparisons.append({
                "id": politician.id,
                "full_name": politician.full_name,
                "party": politician.current_party,
                "state": politician.current_state,
                "chamber": politician.current_chamber,
                "constituency": politician.current_constituency,
                "photo_url": politician.photo_url,
                "scores": {
                    "overall": score.overall_score if score else None,
                    "participation": score.participation_score if score else None,
                    "disclosure": score.disclosure_score if score else None,
                    "integrity_risk": score.integrity_risk_adjustment if score else None,
                },
                "activity": {
                    "avg_attendance": round(avg_attendance, 1) if avg_attendance else None,
                    "total_questions": total_questions,
                    "total_debates": total_debates,
                },
                "disclosure": {
                    "total_assets": disclosure.total_assets if disclosure else None,
                    "total_liabilities": disclosure.total_liabilities if disclosure else None,
                    "criminal_cases": disclosure.criminal_cases if disclosure else None,
                } if disclosure else None,
            })

        return {"politicians": comparisons}
