from app.infrastructure.scoring.strategies.base import ScoringStrategy


class ParticipationStrategy(ScoringStrategy):
    """
    Participation Score (60% weight) — v2
    Measures visible parliamentary activity: attendance, questions, debates.
    Normalized against chamber/session baselines.
    Committees removed (always 0 in data), PAN removed from disclosure.
    """

    SUB_WEIGHTS = {
        "attendance": 0.40,
        "questions": 0.30,
        "debates": 0.30,
    }

    @property
    def weight(self) -> float:
        return 0.60

    @property
    def name(self) -> str:
        return "participation"

    def compute(self, data: dict, baselines: dict | None = None) -> tuple[float, dict]:
        baselines = baselines or {}
        breakdown = {}

        # Attendance: direct percentage (0-100)
        attendance = data.get("attendance_percentage", 0) or 0
        breakdown["attendance"] = {
            "raw": attendance,
            "baseline": baselines.get("avg_attendance", 0),
            "score": min(attendance, 100),
        }

        # Questions: normalize against chamber average
        questions = data.get("questions_asked", 0) or 0
        avg_q = baselines.get("avg_questions", 1) or 1
        q_ratio = min(questions / avg_q, 3.0) if avg_q > 0 else 0
        q_score = min(q_ratio * (100 / 3), 100)
        breakdown["questions"] = {
            "raw": questions,
            "baseline": avg_q,
            "ratio": round(q_ratio, 2),
            "score": round(q_score, 1),
        }

        # Debates: normalize against chamber average
        debates = data.get("debates_participated", 0) or 0
        avg_d = baselines.get("avg_debates", 1) or 1
        d_ratio = min(debates / avg_d, 3.0) if avg_d > 0 else 0
        d_score = min(d_ratio * (100 / 3), 100)
        breakdown["debates"] = {
            "raw": debates,
            "baseline": avg_d,
            "ratio": round(d_ratio, 2),
            "score": round(d_score, 1),
        }

        # Weighted sum
        total = (
            breakdown["attendance"]["score"] * self.SUB_WEIGHTS["attendance"]
            + breakdown["questions"]["score"] * self.SUB_WEIGHTS["questions"]
            + breakdown["debates"]["score"] * self.SUB_WEIGHTS["debates"]
        )

        breakdown["total"] = round(total, 2)
        breakdown["sub_weights"] = self.SUB_WEIGHTS

        return round(total, 2), breakdown
