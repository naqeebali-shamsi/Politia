"""Tests for fake repository implementations — ensures they honor the interface contract."""
import pytest

from tests.factories import make_politician, make_score, make_activity, make_disclosure, make_election


class TestFakePoliticianRepository:
    def test_create_assigns_id(self, politician_repo):
        p = politician_repo.create(make_politician())
        assert p.id is not None
        assert p.id == 1

    def test_get_by_id(self, politician_repo):
        created = politician_repo.create(make_politician())
        found = politician_repo.get_by_id(created.id)
        assert found is not None
        assert found.full_name == created.full_name

    def test_get_by_id_not_found(self, politician_repo):
        assert politician_repo.get_by_id(999) is None

    def test_count(self, politician_repo):
        assert politician_repo.count() == 0
        politician_repo.create(make_politician())
        assert politician_repo.count() == 1

    def test_delete(self, politician_repo):
        p = politician_repo.create(make_politician())
        assert politician_repo.delete(p.id) is True
        assert politician_repo.get_by_id(p.id) is None
        assert politician_repo.count() == 0

    def test_delete_nonexistent(self, politician_repo):
        assert politician_repo.delete(999) is False

    def test_update(self, politician_repo):
        p = politician_repo.create(make_politician(full_name="Original"))
        p.full_name = "Updated"
        updated = politician_repo.update(p)
        assert updated.full_name == "Updated"
        assert politician_repo.get_by_id(p.id).full_name == "Updated"

    def test_update_nonexistent_raises(self, politician_repo):
        p = make_politician(id=999)
        with pytest.raises(ValueError):
            politician_repo.update(p)

    def test_search_by_name(self, politician_repo, sample_politicians):
        results = politician_repo.search(query="Gandhi")
        assert len(results) == 2  # Rahul + Sonia

    def test_search_by_constituency(self, politician_repo, sample_politicians):
        results = politician_repo.search(query="Varanasi")
        assert len(results) == 1

    def test_search_combined_filters(self, politician_repo, sample_politicians):
        results = politician_repo.search(party="BJP", chamber="Lok Sabha")
        assert len(results) == 1  # Only Modi

    def test_bulk_create(self, politician_repo):
        politicians = [make_politician(full_name=f"MP {i}") for i in range(5)]
        created = politician_repo.bulk_create(politicians)
        assert len(created) == 5
        assert politician_repo.count() == 5

    def test_get_distinct_states(self, politician_repo, sample_politicians):
        states = politician_repo.get_distinct_states()
        assert "Gujarat" in states
        assert "Kerala" in states

    def test_get_distinct_parties(self, politician_repo, sample_politicians):
        parties = politician_repo.get_distinct_parties()
        assert "BJP" in parties
        assert "INC" in parties
        assert "TMC" in parties

    def test_get_by_external_id(self, politician_repo):
        p = make_politician(tcpd_id="TCPD_001")
        politician_repo.create(p)
        found = politician_repo.get_by_external_id("tcpd", "TCPD_001")
        assert found is not None
        assert found.tcpd_id == "TCPD_001"

    def test_get_by_external_id_not_found(self, politician_repo):
        assert politician_repo.get_by_external_id("tcpd", "NONEXISTENT") is None


class TestFakeScoreRepository:
    def test_create_and_get(self, score_repo):
        s = score_repo.create(make_score(politician_id=1))
        assert s.id is not None
        assert score_repo.get_by_id(s.id) is not None

    def test_get_current_score(self, score_repo):
        score_repo.create(make_score(politician_id=1, is_current=False))
        current = score_repo.create(make_score(politician_id=1, is_current=True))
        found = score_repo.get_current_score(1)
        assert found is not None
        assert found.id == current.id

    def test_get_current_score_none(self, score_repo):
        assert score_repo.get_current_score(999) is None

    def test_leaderboard_sorted(self, score_repo):
        score_repo.create(make_score(politician_id=1, overall_score=60.0))
        score_repo.create(make_score(politician_id=2, overall_score=80.0))
        score_repo.create(make_score(politician_id=3, overall_score=70.0))

        board = score_repo.get_leaderboard()
        scores = [s.overall_score for _, s in board]
        assert scores == [80.0, 70.0, 60.0]

    def test_get_scores_for_politicians(self, score_repo):
        score_repo.create(make_score(politician_id=1, overall_score=80.0))
        score_repo.create(make_score(politician_id=2, overall_score=70.0))

        result = score_repo.get_scores_for_politicians([1, 2, 3])
        assert 1 in result
        assert 2 in result
        assert 3 not in result

    def test_invalidate_current_scores(self, score_repo):
        score_repo.create(make_score(politician_id=1, is_current=True))
        score_repo.create(make_score(politician_id=2, is_current=True))

        count = score_repo.invalidate_current_scores([1])
        assert count == 1
        assert score_repo.get_current_score(1) is None
        assert score_repo.get_current_score(2) is not None
