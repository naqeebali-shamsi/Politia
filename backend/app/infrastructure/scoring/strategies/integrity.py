from app.infrastructure.scoring.strategies.base import ScoringStrategy


class IntegrityStrategy(ScoringStrategy):
    """
    Integrity Risk Adjustment (15% weight)
    Based ONLY on self-declared official disclosures from affidavits.
    This is an adjustment, not a moral verdict.
    Higher score = lower risk = better.
    """

    @property
    def weight(self) -> float:
        return 0.15

    @property
    def name(self) -> str:
        return "integrity"

    def compute(self, data: dict, baselines: dict | None = None) -> tuple[float, dict]:
        breakdown = {}

        criminal_cases = data.get("criminal_cases", 0) or 0
        serious_cases = data.get("serious_criminal_cases", 0) or 0

        # Start at 100, deduct for cases
        # Each case deducts points, serious cases deduct more
        deduction = 0

        # Regular cases: -10 each, capped at 50
        regular_deduction = min(criminal_cases * 10, 50)
        deduction += regular_deduction
        breakdown["criminal_cases"] = {
            "count": criminal_cases,
            "deduction": regular_deduction,
            "note": "Self-declared cases from affidavit, NOT convictions",
        }

        # Serious cases: additional -15 each, capped at 50
        serious_deduction = min(serious_cases * 15, 50)
        deduction += serious_deduction
        breakdown["serious_criminal_cases"] = {
            "count": serious_cases,
            "additional_deduction": serious_deduction,
        }

        score = max(100 - deduction, 0)
        breakdown["total_deduction"] = deduction
        breakdown["total"] = score
        breakdown["disclaimer"] = (
            "Based on self-declared cases from election affidavits. "
            "These are disclosures, not convictions. "
            "A case count of zero may mean no cases OR incomplete disclosure."
        )

        return round(score, 2), breakdown
