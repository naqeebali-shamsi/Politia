from app.infrastructure.scoring.strategies.base import ScoringStrategy


class IntegrityStrategy(ScoringStrategy):
    """
    Integrity Risk Adjustment (15% weight) — v2
    Based ONLY on self-declared official disclosures from affidavits.
    This is an adjustment, not a moral verdict.
    Higher score = lower risk = better.

    CRITICAL v2 change: No disclosure data → score 0 (not 100).
    "No data" is NOT "no risk." Only a filed affidavit with zero cases gets 100.
    """

    @property
    def weight(self) -> float:
        return 0.15

    @property
    def name(self) -> str:
        return "integrity"

    def compute(self, data: dict, baselines: dict | None = None) -> tuple[float, dict]:
        breakdown = {}

        has_disclosure = data.get("has_disclosure", False)

        # If no disclosure data exists, integrity is unknown → score 0
        if not has_disclosure:
            breakdown["has_disclosure"] = False
            breakdown["total"] = 0
            breakdown["note"] = "No affidavit data available — integrity cannot be assessed"
            return 0.0, breakdown

        criminal_cases = data.get("criminal_cases", 0) or 0

        # Start at 100, deduct for cases
        deduction = 0

        # Cases: -10 each, capped at 50
        case_deduction = min(criminal_cases * 10, 50)
        deduction += case_deduction
        breakdown["criminal_cases"] = {
            "count": criminal_cases,
            "deduction": case_deduction,
            "note": "Self-declared cases from affidavit, NOT convictions",
        }

        score = max(100 - deduction, 0)
        breakdown["has_disclosure"] = True
        breakdown["total_deduction"] = deduction
        breakdown["total"] = score
        breakdown["disclaimer"] = (
            "Based on self-declared cases from election affidavits. "
            "These are disclosures, not convictions."
        )

        return round(score, 2), breakdown
