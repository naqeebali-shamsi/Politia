"""
P0-4+5 TDD Tests: Scoring Formula Fixes

Tests for:
- Remove ghost fields (committee_memberships, pan_declared, serious_criminal_cases)
- Fix integrity-rewards-ignorance (no data ≠ no risk)
- Formula version bump to v2
- Nondeterministic scoring fix
"""
import pytest
from app.infrastructure.scoring.engine import ScoringEngine
from app.infrastructure.scoring.strategies.participation import ParticipationStrategy
from app.infrastructure.scoring.strategies.disclosure import DisclosureStrategy
from app.infrastructure.scoring.strategies.integrity import IntegrityStrategy


class TestGhostFieldRemoval:
    """Ghost fields (committee, PAN, serious_criminal_cases) must not affect scores."""

    def test_participation_max_score_is_100(self):
        """With ghost fields removed, perfect activity data should achieve 100."""
        strategy = ParticipationStrategy()
        score, breakdown = strategy.compute(
            {"attendance_percentage": 100, "questions_asked": 300,
             "debates_participated": 150},
            {"avg_attendance": 70, "avg_questions": 100, "avg_debates": 50},
        )
        assert score == 100.0, f"Max participation should be 100, got {score}"

    def test_participation_sub_weights_sum_to_one(self):
        strategy = ParticipationStrategy()
        total = sum(strategy.SUB_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_participation_has_no_committee_weight(self):
        strategy = ParticipationStrategy()
        assert "committees" not in strategy.SUB_WEIGHTS

    def test_disclosure_max_score_is_100(self):
        """With PAN removed, full disclosure should achieve 100."""
        strategy = DisclosureStrategy()
        score, breakdown = strategy.compute({
            "affidavit_complete": True,
            "total_assets": 50_000_000,
            "total_liabilities": 1_000_000,
            "election_count": 3,
        })
        assert score == 100.0, f"Max disclosure should be 100, got {score}"

    def test_disclosure_has_no_pan_field(self):
        """PAN field should not exist in disclosure breakdown."""
        strategy = DisclosureStrategy()
        _, breakdown = strategy.compute({
            "affidavit_complete": True,
            "total_assets": 50_000_000,
        })
        assert "pan_declared" not in breakdown


class TestIntegrityNoDataHandling:
    """No data should NOT give a perfect integrity score."""

    def test_no_disclosure_gives_zero_integrity(self):
        """A politician with no disclosure data should get integrity=0, not 100."""
        strategy = IntegrityStrategy()
        score, breakdown = strategy.compute({"has_disclosure": False})
        assert score == 0.0, f"No disclosure data should give 0 integrity, got {score}"

    def test_disclosure_with_zero_cases_gives_full_score(self):
        """Filed affidavit with zero cases IS legitimate full integrity."""
        strategy = IntegrityStrategy()
        score, _ = strategy.compute({"has_disclosure": True, "criminal_cases": 0})
        assert score == 100.0

    def test_disclosure_with_cases_still_deducts(self):
        strategy = IntegrityStrategy()
        score, _ = strategy.compute({"has_disclosure": True, "criminal_cases": 3})
        assert score < 100.0


class TestFormulaVersionBump:
    """New scoring formula should be v2."""

    def test_engine_version_is_v2(self):
        engine = ScoringEngine()
        assert engine.VERSION == "v2"

    def test_computed_scores_have_v2(self):
        engine = ScoringEngine()
        score = engine.compute_score(
            politician_id=1,
            participation_data={"attendance_percentage": 80},
            disclosure_data={"affidavit_complete": True, "total_assets": 1000},
            integrity_data={"has_disclosure": True, "criminal_cases": 0},
        )
        assert score.formula_version == "v2"


class TestOverallScoreCorrectness:
    """The overall score must be the weighted sum of components."""

    def test_perfect_mp_scores_100(self):
        engine = ScoringEngine()
        score = engine.compute_score(
            politician_id=1,
            participation_data={"attendance_percentage": 100, "questions_asked": 300,
                                "debates_participated": 150},
            disclosure_data={"affidavit_complete": True, "total_assets": 50_000_000,
                             "total_liabilities": 1_000_000, "election_count": 5},
            integrity_data={"has_disclosure": True, "criminal_cases": 0},
            baselines={"avg_attendance": 70, "avg_questions": 100, "avg_debates": 50},
        )
        assert abs(score.overall_score - 100.0) < 1.0

    def test_no_data_mp_scores_zero(self):
        """A politician with zero data across all dimensions should score 0."""
        engine = ScoringEngine()
        score = engine.compute_score(
            politician_id=1,
            participation_data={},
            disclosure_data={},
            integrity_data={"has_disclosure": False},
        )
        assert score.overall_score == 0.0, f"No data should give 0, got {score.overall_score}"

    def test_overall_is_weighted_sum(self):
        engine = ScoringEngine()
        score = engine.compute_score(
            politician_id=1,
            participation_data={"attendance_percentage": 80, "questions_asked": 50,
                                "debates_participated": 25},
            disclosure_data={"affidavit_complete": True, "total_assets": 10_000_000,
                             "election_count": 2},
            integrity_data={"has_disclosure": True, "criminal_cases": 1},
            baselines={"avg_attendance": 70, "avg_questions": 100, "avg_debates": 50},
        )
        expected = (
            score.participation_score * 0.60
            + score.disclosure_score * 0.25
            + score.integrity_risk_adjustment * 0.15
        )
        assert abs(score.overall_score - round(expected, 2)) < 0.5
