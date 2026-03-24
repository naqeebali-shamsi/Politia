"""
P0-2 TDD Tests: Data Sufficiency Gates

Politicians without meaningful data should NOT receive scores.
The API should return a data_coverage field indicating data richness.
"""
import pytest
from app.infrastructure.scoring.engine import ScoringEngine


class TestDataSufficiencyThreshold:
    """Define what counts as 'sufficient data' for scoring."""

    def test_election_only_is_insufficient(self):
        """Having only election records (no activity, no disclosure) = no score."""
        from app.infrastructure.scoring.engine import has_sufficient_data

        assert has_sufficient_data(
            has_activity=False, has_disclosure=False
        ) is False

    def test_activity_only_is_sufficient(self):
        from app.infrastructure.scoring.engine import has_sufficient_data

        assert has_sufficient_data(
            has_activity=True, has_disclosure=False
        ) is True

    def test_disclosure_only_is_sufficient(self):
        from app.infrastructure.scoring.engine import has_sufficient_data

        assert has_sufficient_data(
            has_activity=False, has_disclosure=True
        ) is True

    def test_both_is_sufficient(self):
        from app.infrastructure.scoring.engine import has_sufficient_data

        assert has_sufficient_data(
            has_activity=True, has_disclosure=True
        ) is True


class TestDataCoverageComputation:
    """Compute a data coverage score (0-100) indicating how much data backs a profile."""

    def test_no_data_gives_minimal_coverage(self):
        """Election-only gives minimal coverage (just proves person exists)."""
        from app.infrastructure.scoring.engine import compute_data_coverage

        coverage = compute_data_coverage(
            has_activity=False, has_disclosure=False, election_count=0
        )
        assert coverage == 0

        coverage_with_election = compute_data_coverage(
            has_activity=False, has_disclosure=False, election_count=1
        )
        assert 0 < coverage_with_election <= 10

    def test_election_only_gives_low_coverage(self):
        from app.infrastructure.scoring.engine import compute_data_coverage

        coverage = compute_data_coverage(
            has_activity=False, has_disclosure=False, election_count=3
        )
        assert 0 < coverage <= 20

    def test_full_data_gives_high_coverage(self):
        from app.infrastructure.scoring.engine import compute_data_coverage

        coverage = compute_data_coverage(
            has_activity=True, has_disclosure=True, election_count=5
        )
        assert coverage >= 80

    def test_partial_data_gives_medium_coverage(self):
        from app.infrastructure.scoring.engine import compute_data_coverage

        coverage = compute_data_coverage(
            has_activity=True, has_disclosure=False, election_count=2
        )
        assert 20 < coverage < 80


class TestScoringWithSufficiencyGate:
    """The scoring engine should respect data sufficiency."""

    def test_engine_returns_none_for_insufficient_data(self):
        engine = ScoringEngine()
        result = engine.compute_score_if_sufficient(
            politician_id=1,
            participation_data={},
            disclosure_data={},
            integrity_data={"has_disclosure": False},
            has_activity=False,
            has_disclosure=False,
        )
        assert result is None

    def test_engine_returns_score_for_sufficient_data(self):
        engine = ScoringEngine()
        result = engine.compute_score_if_sufficient(
            politician_id=1,
            participation_data={"attendance_percentage": 80},
            disclosure_data={"affidavit_complete": True, "total_assets": 1000000},
            integrity_data={"has_disclosure": True, "criminal_cases": 0},
            has_activity=True,
            has_disclosure=True,
            baselines={"avg_attendance": 70, "avg_questions": 100, "avg_debates": 50},
        )
        assert result is not None
        assert result.overall_score > 0
