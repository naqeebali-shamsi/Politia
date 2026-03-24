"""Comprehensive tests for the scoring engine and all strategies."""
import pytest

from app.infrastructure.scoring.engine import ScoringEngine
from app.infrastructure.scoring.strategies.participation import ParticipationStrategy
from app.infrastructure.scoring.strategies.disclosure import DisclosureStrategy
from app.infrastructure.scoring.strategies.integrity import IntegrityStrategy


class TestParticipationStrategy:
    @pytest.fixture
    def strategy(self):
        return ParticipationStrategy()

    def test_weight_is_60_percent(self, strategy):
        assert strategy.weight == 0.60

    def test_name(self, strategy):
        assert strategy.name == "participation"

    def test_perfect_attendance(self, strategy):
        score, breakdown = strategy.compute(
            {"attendance_percentage": 100, "questions_asked": 90,
             "debates_participated": 45, "committee_memberships": 4},
            {"avg_attendance": 70, "avg_questions": 30, "avg_debates": 15},
        )
        assert score > 0
        assert breakdown["attendance"]["score"] == 100

    def test_zero_data(self, strategy):
        """All zeros should produce zero score, not errors."""
        score, breakdown = strategy.compute(
            {"attendance_percentage": 0, "questions_asked": 0,
             "debates_participated": 0, "committee_memberships": 0},
            {"avg_attendance": 70, "avg_questions": 30, "avg_debates": 15},
        )
        assert score == 0.0
        assert breakdown["total"] == 0.0

    def test_missing_data_fields(self, strategy):
        """Missing fields should not crash, treated as 0."""
        score, breakdown = strategy.compute({}, {})
        assert score == 0.0

    def test_none_values_treated_as_zero(self, strategy):
        score, breakdown = strategy.compute(
            {"attendance_percentage": None, "questions_asked": None,
             "debates_participated": None, "committee_memberships": None},
            {"avg_attendance": 0, "avg_questions": 0, "avg_debates": 0},
        )
        assert score == 0.0

    def test_zero_baselines_no_division_error(self, strategy):
        """Zero baselines must not cause division by zero."""
        score, breakdown = strategy.compute(
            {"attendance_percentage": 50, "questions_asked": 10,
             "debates_participated": 5, "committee_memberships": 1},
            {"avg_attendance": 0, "avg_questions": 0, "avg_debates": 0},
        )
        # Should not raise, should produce a score
        assert isinstance(score, float)

    def test_above_average_capped(self, strategy):
        """Scores should not exceed 100 even with extreme values."""
        score, breakdown = strategy.compute(
            {"attendance_percentage": 200, "questions_asked": 1000,
             "debates_participated": 500, "committee_memberships": 20},
            {"avg_attendance": 70, "avg_questions": 30, "avg_debates": 15},
        )
        # Attendance capped at 100, others capped via ratio cap
        assert breakdown["attendance"]["score"] <= 100
        assert breakdown["questions"]["score"] <= 100
        assert breakdown["debates"]["score"] <= 100
        # committees removed in v2

    def test_sub_weights_sum_to_one(self, strategy):
        total = sum(strategy.SUB_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_breakdown_transparency(self, strategy):
        """Breakdown must contain raw values, baselines, and computed scores."""
        _, breakdown = strategy.compute(
            {"attendance_percentage": 85, "questions_asked": 50,
             "debates_participated": 20, "committee_memberships": 3},
            {"avg_attendance": 70, "avg_questions": 30, "avg_debates": 15},
        )
        assert "attendance" in breakdown
        assert "raw" in breakdown["attendance"]
        assert "baseline" in breakdown["attendance"]
        assert "score" in breakdown["attendance"]
        assert "sub_weights" in breakdown


class TestDisclosureStrategy:
    @pytest.fixture
    def strategy(self):
        return DisclosureStrategy()

    def test_weight_is_25_percent(self, strategy):
        assert strategy.weight == 0.25

    def test_name(self, strategy):
        assert strategy.name == "disclosure"

    def test_full_disclosure(self, strategy):
        score, breakdown = strategy.compute({
            "affidavit_complete": True,
            "total_assets": 50_000_000,
            "total_liabilities": 1_000_000,
            "pan_declared": True,
            "election_count": 3,
        })
        assert score == 100.0
        assert breakdown["total_points"] == breakdown["max_points"]

    def test_no_disclosure(self, strategy):
        score, breakdown = strategy.compute({})
        assert score == 0.0
        assert breakdown["total_points"] == 0

    def test_partial_disclosure(self, strategy):
        score, breakdown = strategy.compute({
            "affidavit_complete": True,
            "total_assets": None,
            "pan_declared": False,
            "election_count": 1,
        })
        assert 0 < score < 100
        assert breakdown["affidavit_complete"]["points"] == 35  # v2: reweighted after PAN removal
        assert breakdown["assets_declared"]["points"] == 0

    def test_election_linkage_capped(self, strategy):
        """Election linkage points should cap at 20."""
        _, breakdown = strategy.compute({"election_count": 100})
        assert breakdown["election_linkage"]["points"] == 20


class TestIntegrityStrategy:
    @pytest.fixture
    def strategy(self):
        return IntegrityStrategy()

    def test_weight_is_15_percent(self, strategy):
        assert strategy.weight == 0.15

    def test_name(self, strategy):
        assert strategy.name == "integrity"

    def test_no_cases_full_score(self, strategy):
        score, breakdown = strategy.compute({"has_disclosure": True, "criminal_cases": 0})
        assert score == 100.0

    def test_one_regular_case(self, strategy):
        score, _ = strategy.compute({"has_disclosure": True, "criminal_cases": 1})
        assert score == 90.0

    def test_many_cases_floor_at_minimum(self, strategy):
        """Score floors at 50 with cap (deduction capped at 50)."""
        score, _ = strategy.compute({"has_disclosure": True, "criminal_cases": 20})
        assert score == 50.0  # 100 - min(20*10, 50) = 50

    def test_missing_data_gives_zero(self, strategy):
        """v2: no disclosure data = 0 integrity (not 100)."""
        score, _ = strategy.compute({})
        assert score == 0.0

    def test_no_disclosure_flag_gives_zero(self, strategy):
        score, _ = strategy.compute({"has_disclosure": False})
        assert score == 0.0

    def test_disclaimer_present(self, strategy):
        """Integrity scores with disclosure data must include disclaimer."""
        _, breakdown = strategy.compute({"has_disclosure": True, "criminal_cases": 0})
        assert "disclaimer" in breakdown
        assert "self-declared" in breakdown["disclaimer"].lower()


class TestScoringEngine:
    @pytest.fixture
    def engine(self):
        return ScoringEngine()

    def test_engine_creates_with_default_strategies(self, engine):
        assert engine.VERSION == "v2"
        assert len(engine._strategies) == 3

    def test_weights_sum_to_one(self, engine):
        total = sum(s.weight for s in engine._strategies)
        assert abs(total - 1.0) < 0.01

    def test_invalid_weights_rejected(self):
        """Engine should reject strategies whose weights don't sum to 1."""
        bad_strategy = ParticipationStrategy()
        with pytest.raises(ValueError, match="weights must sum to 1.0"):
            ScoringEngine(strategies=[bad_strategy])  # Only 0.60, not 1.0

    def test_compute_score_returns_score_record(self, engine):
        result = engine.compute_score(
            politician_id=42,
            participation_data={"attendance_percentage": 85, "questions_asked": 50,
                                "debates_participated": 20, "committee_memberships": 3},
            disclosure_data={"affidavit_complete": True, "total_assets": 50_000_000,
                             "total_liabilities": 1_000_000, "pan_declared": True,
                             "election_count": 3},
            integrity_data={"criminal_cases": 0, "serious_criminal_cases": 0},
            baselines={"avg_attendance": 70, "avg_questions": 30, "avg_debates": 15},
        )
        assert result.politician_id == 42
        assert result.formula_version == "v2"
        assert result.is_current is True
        assert 0 <= result.overall_score <= 100
        assert result.computed_at is not None

    def test_overall_score_is_weighted_sum(self, engine):
        """Overall score must equal sum of (component * weight)."""
        result = engine.compute_score(
            politician_id=1,
            participation_data={"attendance_percentage": 80, "questions_asked": 40,
                                "debates_participated": 15, "committee_memberships": 2},
            disclosure_data={"affidavit_complete": True, "total_assets": 10_000_000,
                             "total_liabilities": 500_000, "pan_declared": True,
                             "election_count": 2},
            integrity_data={"criminal_cases": 1, "serious_criminal_cases": 0},
            baselines={"avg_attendance": 70, "avg_questions": 30, "avg_debates": 15},
        )
        expected = (
            result.participation_score * 0.60
            + result.disclosure_score * 0.25
            + result.integrity_risk_adjustment * 0.15
        )
        assert abs(result.overall_score - round(expected, 2)) < 0.1

    def test_all_zeros_produces_zero(self, engine):
        result = engine.compute_score(
            politician_id=1,
            participation_data={},
            disclosure_data={},
            integrity_data={},
        )
        # v2: Participation=0, Disclosure=0, Integrity=0 (no data = no score)
        # Overall = 0*0.6 + 0*0.25 + 0*0.15 = 0.0
        assert result.participation_score == 0.0
        assert result.disclosure_score == 0.0
        assert result.integrity_risk_adjustment == 0.0
        assert result.overall_score == 0.0

    def test_breakdowns_included(self, engine):
        result = engine.compute_score(
            politician_id=1,
            participation_data={"attendance_percentage": 50},
            disclosure_data={"affidavit_complete": True},
            integrity_data={"criminal_cases": 2},
        )
        assert result.participation_breakdown is not None
        assert result.disclosure_breakdown is not None
        assert result.integrity_breakdown is not None

    def test_perfect_mp(self, engine):
        """An MP with perfect stats should score close to 100."""
        result = engine.compute_score(
            politician_id=1,
            participation_data={"attendance_percentage": 100, "questions_asked": 100,
                                "debates_participated": 50},
            disclosure_data={"affidavit_complete": True, "total_assets": 10_000_000,
                             "total_liabilities": 100_000, "election_count": 5},
            integrity_data={"has_disclosure": True, "criminal_cases": 0},
            baselines={"avg_attendance": 70, "avg_questions": 30, "avg_debates": 15},
        )
        assert result.overall_score >= 85

    def test_worst_case_mp(self, engine):
        """An MP with worst stats should score very low."""
        result = engine.compute_score(
            politician_id=1,
            participation_data={"attendance_percentage": 0, "questions_asked": 0,
                                "debates_participated": 0},
            disclosure_data={},
            integrity_data={"has_disclosure": True, "criminal_cases": 10},
            baselines={"avg_attendance": 70, "avg_questions": 30, "avg_debates": 15},
        )
        assert result.overall_score < 10
