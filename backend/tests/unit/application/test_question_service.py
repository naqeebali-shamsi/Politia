"""Unit tests for QuestionService using fake repositories."""
from datetime import date

from app.application.services.question_service import QuestionService
from tests.factories import make_question


class TestQuestionServiceSearch:
    def test_search_returns_all_when_no_filters(self, question_repo):
        questions = [
            make_question(politician_id=1, ministry="Ministry of Finance"),
            make_question(politician_id=2, ministry="Ministry of Defence"),
            make_question(politician_id=1, ministry="Ministry of Health"),
        ]
        question_repo.bulk_create(questions)
        service = QuestionService(question_repo)

        result = service.search()
        assert result["total"] == 3
        assert len(result["results"]) == 3

    def test_search_filters_by_politician_id(self, question_repo):
        question_repo.bulk_create([
            make_question(politician_id=1),
            make_question(politician_id=2),
            make_question(politician_id=1),
        ])
        service = QuestionService(question_repo)

        result = service.search(politician_id=1)
        assert result["total"] == 2
        assert all(r.politician_id == 1 for r in result["results"])

    def test_search_filters_by_ministry(self, question_repo):
        question_repo.bulk_create([
            make_question(ministry="Ministry of Finance"),
            make_question(ministry="Ministry of Defence"),
            make_question(ministry="Ministry of Finance"),
        ])
        service = QuestionService(question_repo)

        result = service.search(ministry="Finance")
        assert result["total"] == 2

    def test_search_filters_by_term(self, question_repo):
        question_repo.bulk_create([
            make_question(term_number=17),
            make_question(term_number=18),
            make_question(term_number=17),
        ])
        service = QuestionService(question_repo)

        result = service.search(term=17)
        assert result["total"] == 2

    def test_search_filters_by_query(self, question_repo):
        question_repo.bulk_create([
            make_question(question_title="Status of bank NPA resolution"),
            make_question(question_title="Railway budget allocation"),
            make_question(question_title="NPA recovery status"),
        ])
        service = QuestionService(question_repo)

        result = service.search(query="NPA")
        assert result["total"] == 2

    def test_search_respects_pagination(self, question_repo):
        for i in range(10):
            question_repo.create(make_question(politician_id=i))
        service = QuestionService(question_repo)

        result = service.search(offset=3, limit=4)
        assert result["offset"] == 3
        assert result["limit"] == 4
        assert len(result["results"]) == 4


class TestQuestionServiceStats:
    def test_get_stats_returns_ministry_and_term_breakdown(self, question_repo):
        question_repo.bulk_create([
            make_question(ministry="Ministry of Finance", term_number=17),
            make_question(ministry="Ministry of Finance", term_number=17),
            make_question(ministry="Ministry of Defence", term_number=18),
        ])
        service = QuestionService(question_repo)

        stats = service.get_stats()
        assert stats["total"] == 3
        assert len(stats["by_ministry"]) == 2
        assert stats["by_ministry"][0]["ministry"] == "Ministry of Finance"
        assert stats["by_ministry"][0]["count"] == 2
        assert len(stats["by_term"]) == 2
        assert "Ministry of Defence" in stats["ministries"]
        assert "Ministry of Finance" in stats["ministries"]

    def test_get_stats_empty_repo(self, question_repo):
        service = QuestionService(question_repo)
        stats = service.get_stats()
        assert stats["total"] == 0
        assert stats["by_ministry"] == []
        assert stats["by_term"] == []
