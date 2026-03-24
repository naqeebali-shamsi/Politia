from datetime import datetime, timezone

from app.domain.entities.score import ScoreRecord
from app.infrastructure.scoring.strategies.base import ScoringStrategy
from app.infrastructure.scoring.strategies.participation import ParticipationStrategy
from app.infrastructure.scoring.strategies.disclosure import DisclosureStrategy
from app.infrastructure.scoring.strategies.integrity import IntegrityStrategy


def has_sufficient_data(has_activity: bool, has_disclosure: bool) -> bool:
    """A politician needs at least one non-election data source to be scored."""
    return has_activity or has_disclosure


def compute_data_coverage(
    has_activity: bool, has_disclosure: bool, election_count: int = 0,
) -> int:
    """
    Compute a 0-100 data coverage score indicating how much data backs a profile.
    Used as a confidence indicator alongside the accountability score.
    """
    coverage = 0

    # Election records: up to 15 points
    coverage += min(election_count * 5, 15)

    # Activity data: 45 points
    if has_activity:
        coverage += 45

    # Disclosure data: 40 points
    if has_disclosure:
        coverage += 40

    return min(coverage, 100)


class ScoringEngine:
    """
    Computes accountability scores using pluggable strategies.
    New score components can be added by implementing ScoringStrategy.
    Formula versioning ensures reproducibility.
    """

    VERSION = "v2"

    def __init__(self, strategies: list[ScoringStrategy] | None = None):
        self._strategies = strategies or [
            ParticipationStrategy(),
            DisclosureStrategy(),
            IntegrityStrategy(),
        ]
        # Validate weights sum to ~1.0
        total_weight = sum(s.weight for s in self._strategies)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Strategy weights must sum to 1.0, got {total_weight}")

    def compute_score(
        self,
        politician_id: int,
        participation_data: dict,
        disclosure_data: dict,
        integrity_data: dict,
        baselines: dict | None = None,
    ) -> ScoreRecord:
        data_map = {
            "participation": participation_data,
            "disclosure": disclosure_data,
            "integrity": integrity_data,
        }

        component_scores = {}
        component_breakdowns = {}

        for strategy in self._strategies:
            data = data_map.get(strategy.name, {})
            score_value, breakdown = strategy.compute(data, baselines)
            component_scores[strategy.name] = score_value
            component_breakdowns[strategy.name] = breakdown

        # Weighted overall score
        overall = sum(
            component_scores[s.name] * s.weight
            for s in self._strategies
        )

        return ScoreRecord(
            politician_id=politician_id,
            overall_score=round(overall, 2),
            participation_score=component_scores.get("participation", 0),
            disclosure_score=component_scores.get("disclosure", 0),
            integrity_risk_adjustment=component_scores.get("integrity", 0),
            participation_breakdown=component_breakdowns.get("participation"),
            disclosure_breakdown=component_breakdowns.get("disclosure"),
            integrity_breakdown=component_breakdowns.get("integrity"),
            formula_version=self.VERSION,
            computed_at=datetime.now(timezone.utc),
            is_current=True,
        )

    def compute_score_if_sufficient(
        self,
        politician_id: int,
        participation_data: dict,
        disclosure_data: dict,
        integrity_data: dict,
        has_activity: bool = False,
        has_disclosure: bool = False,
        baselines: dict | None = None,
    ) -> ScoreRecord | None:
        """Compute score only if sufficient data exists. Returns None otherwise."""
        if not has_sufficient_data(has_activity, has_disclosure):
            return None
        return self.compute_score(
            politician_id, participation_data, disclosure_data, integrity_data, baselines,
        )
