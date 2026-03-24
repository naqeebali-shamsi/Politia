from app.infrastructure.scoring.strategies.base import ScoringStrategy


class DisclosureStrategy(ScoringStrategy):
    """
    Disclosure Score (25% weight)
    Measures completeness and availability of public disclosures.
    """

    @property
    def weight(self) -> float:
        return 0.25

    @property
    def name(self) -> str:
        return "disclosure"

    def compute(self, data: dict, baselines: dict | None = None) -> tuple[float, dict]:
        breakdown = {}
        points = 0
        max_points = 0

        # Affidavit filed and complete
        max_points += 30
        affidavit_complete = data.get("affidavit_complete", False)
        affidavit_points = 30 if affidavit_complete else 0
        points += affidavit_points
        breakdown["affidavit_complete"] = {"value": affidavit_complete, "points": affidavit_points}

        # Assets declared
        max_points += 20
        has_assets = data.get("total_assets") is not None and data.get("total_assets", 0) >= 0
        asset_points = 20 if has_assets else 0
        points += asset_points
        breakdown["assets_declared"] = {"value": has_assets, "points": asset_points}

        # Liabilities declared
        max_points += 15
        has_liabilities = data.get("total_liabilities") is not None
        liability_points = 15 if has_liabilities else 0
        points += liability_points
        breakdown["liabilities_declared"] = {"value": has_liabilities, "points": liability_points}

        # PAN declared
        max_points += 15
        pan = data.get("pan_declared", False)
        pan_points = 15 if pan else 0
        points += pan_points
        breakdown["pan_declared"] = {"value": pan, "points": pan_points}

        # Election record linkage (has multiple election records)
        max_points += 20
        election_count = data.get("election_count", 0)
        linkage_points = min(election_count * 10, 20)
        points += linkage_points
        breakdown["election_linkage"] = {"elections_found": election_count, "points": linkage_points}

        score = (points / max_points * 100) if max_points > 0 else 0

        breakdown["total_points"] = points
        breakdown["max_points"] = max_points
        breakdown["total"] = round(score, 2)

        return round(score, 2), breakdown
