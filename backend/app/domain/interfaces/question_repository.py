from abc import abstractmethod

from app.domain.entities.question import QuestionRecord
from app.domain.interfaces.base_repository import BaseRepository


class QuestionRepository(BaseRepository[QuestionRecord]):
    @abstractmethod
    def search(
        self,
        politician_id: int | None = None,
        ministry: str | None = None,
        term: int | None = None,
        query: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[QuestionRecord]:
        ...

    @abstractmethod
    def search_count(
        self,
        politician_id: int | None = None,
        ministry: str | None = None,
        term: int | None = None,
        query: str | None = None,
    ) -> int:
        ...

    @abstractmethod
    def get_stats_by_ministry(self) -> list[dict]:
        """Returns [{ministry, count}] ordered by count desc."""
        ...

    @abstractmethod
    def get_stats_by_term(self) -> list[dict]:
        """Returns [{term_number, count}] ordered by term."""
        ...

    @abstractmethod
    def get_distinct_ministries(self) -> list[str]:
        ...

    @abstractmethod
    def bulk_create(self, records: list[QuestionRecord]) -> list[QuestionRecord]:
        ...
