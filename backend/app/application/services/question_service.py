from app.domain.interfaces.question_repository import QuestionRepository


class QuestionService:
    def __init__(self, question_repo: QuestionRepository):
        self._questions = question_repo

    def search(
        self,
        politician_id: int | None = None,
        ministry: str | None = None,
        term: int | None = None,
        query: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict:
        results = self._questions.search(
            politician_id=politician_id,
            ministry=ministry,
            term=term,
            query=query,
            offset=offset,
            limit=limit,
        )
        total = self._questions.search_count(
            politician_id=politician_id,
            ministry=ministry,
            term=term,
            query=query,
        )
        return {
            "results": results,
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    def get_stats(self) -> dict:
        return {
            "by_ministry": self._questions.get_stats_by_ministry(),
            "by_term": self._questions.get_stats_by_term(),
            "total": self._questions.count(),
            "ministries": self._questions.get_distinct_ministries(),
        }
