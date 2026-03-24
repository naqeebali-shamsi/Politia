"""Tests for application services using fake repositories."""
import pytest

from app.application.services.politician_service import PoliticianService
from app.application.services.leaderboard_service import LeaderboardService
from app.application.services.comparison_service import ComparisonService
from tests.fakes import FakeElectionRepository


class TestPoliticianService:
    @pytest.fixture
    def service(self, politician_repo, score_repo, activity_repo, disclosure_repo):
        election_repo = FakeElectionRepository()
        return PoliticianService(politician_repo, score_repo, activity_repo, disclosure_repo, election_repo)

    def test_search_returns_empty_on_no_data(self, service):
        result = service.search(query="test")
        assert result["results"] == []
        assert result["total"] == 0

    def test_search_finds_by_name(self, service, sample_politicians, sample_scores):
        result = service.search(query="Modi")
        assert result["total"] == 1
        assert result["results"][0]["full_name"] == "Narendra Modi"

    def test_search_includes_scores(self, service, sample_politicians, sample_scores):
        result = service.search(query="Modi")
        assert result["results"][0]["score"] is not None

    def test_search_filters_by_state(self, service, sample_politicians):
        result = service.search(state="Gujarat")
        assert result["total"] == 2  # Modi + Amit Shah

    def test_search_filters_by_party(self, service, sample_politicians):
        result = service.search(party="INC")
        assert result["total"] == 2  # Rahul + Sonia

    def test_search_filters_by_chamber(self, service, sample_politicians):
        result = service.search(chamber="Rajya Sabha")
        assert result["total"] == 2  # Amit Shah + Sonia

    def test_search_filters_by_active_status(self, service, sample_politicians):
        result = service.search(is_active=False)
        assert result["total"] == 1
        assert result["results"][0]["full_name"] == "Sonia Gandhi"

    def test_search_pagination(self, service, sample_politicians):
        page1 = service.search(limit=2)
        page2 = service.search(offset=2, limit=2)
        assert len(page1["results"]) == 2
        assert len(page2["results"]) == 2
        # Different politicians on each page
        names1 = {r["full_name"] for r in page1["results"]}
        names2 = {r["full_name"] for r in page2["results"]}
        assert len(names1 & names2) == 0

    def test_get_profile_returns_none_for_missing(self, service):
        result = service.get_profile(999)
        assert result is None

    def test_get_profile_returns_full_data(self, service, sample_politicians, sample_scores,
                                            sample_activities, sample_disclosures):
        pid = sample_politicians[0].id
        profile = service.get_profile(pid)
        assert profile is not None
        assert profile["politician"].full_name == "Narendra Modi"
        assert profile["score"] is not None
        assert len(profile["activities"]) > 0
        assert len(profile["disclosures"]) > 0

    def test_get_filters(self, service, sample_politicians):
        filters = service.get_filters()
        assert "Gujarat" in filters["states"]
        assert "BJP" in filters["parties"]
        assert "INC" in filters["parties"]


class TestLeaderboardService:
    @pytest.fixture
    def service(self, politician_repo, score_repo):
        return LeaderboardService(politician_repo, score_repo)

    def test_empty_leaderboard(self, service):
        result = service.get_leaderboard()
        assert result["results"] == []

    def test_leaderboard_sorted_by_score(self, service, sample_politicians, sample_scores):
        result = service.get_leaderboard()
        scores = [r["score"] for r in result["results"]]
        assert scores == sorted(scores, reverse=True)

    def test_leaderboard_respects_limit(self, service, sample_politicians, sample_scores):
        result = service.get_leaderboard(limit=2)
        assert len(result["results"]) == 2

    def test_leaderboard_includes_rank(self, service, sample_politicians, sample_scores):
        result = service.get_leaderboard()
        assert result["results"][0]["rank"] == 1
        assert result["results"][1]["rank"] == 2

    def test_invalid_sort_falls_back(self, service, sample_politicians, sample_scores):
        """Invalid sort_by should fall back to overall_score."""
        result = service.get_leaderboard(sort_by="invalid_field")
        assert len(result["results"]) > 0


class TestComparisonService:
    @pytest.fixture
    def service(self, politician_repo, score_repo, activity_repo, disclosure_repo):
        return ComparisonService(politician_repo, score_repo, activity_repo, disclosure_repo)

    def test_compare_too_few_raises(self, service):
        with pytest.raises(ValueError, match="at least 2"):
            service.compare([1])

    def test_compare_too_many_raises(self, service):
        with pytest.raises(ValueError, match="more than 5"):
            service.compare([1, 2, 3, 4, 5, 6])

    def test_compare_two_politicians(self, service, sample_politicians, sample_scores,
                                      sample_activities, sample_disclosures):
        ids = [sample_politicians[0].id, sample_politicians[1].id]
        result = service.compare(ids)
        assert len(result["politicians"]) == 2
        names = {p["full_name"] for p in result["politicians"]}
        assert "Narendra Modi" in names
        assert "Rahul Gandhi" in names

    def test_compare_includes_scores(self, service, sample_politicians, sample_scores):
        ids = [sample_politicians[0].id, sample_politicians[1].id]
        result = service.compare(ids)
        for p in result["politicians"]:
            assert "scores" in p
            assert p["scores"]["overall"] is not None

    def test_compare_handles_missing_politicians(self, service, sample_politicians, sample_scores):
        """Non-existent IDs should be silently skipped."""
        ids = [sample_politicians[0].id, 99999]
        result = service.compare(ids)
        assert len(result["politicians"]) == 1

    def test_compare_includes_activity_aggregates(self, service, sample_politicians,
                                                    sample_scores, sample_activities):
        ids = [sample_politicians[0].id, sample_politicians[1].id]
        result = service.compare(ids)
        for p in result["politicians"]:
            if p["activity"]:
                assert "avg_attendance" in p["activity"]
                assert "total_questions" in p["activity"]

    def test_compare_handles_no_disclosures(self, service, sample_politicians, sample_scores):
        """Politicians without disclosures should show null."""
        ids = [sample_politicians[3].id, sample_politicians[4].id]  # No disclosures created
        result = service.compare(ids)
        for p in result["politicians"]:
            assert p["disclosure"] is None
