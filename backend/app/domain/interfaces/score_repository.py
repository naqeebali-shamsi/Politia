from abc import abstractmethod

from app.domain.entities.score import ScoreRecord
from app.domain.interfaces.base_repository import BaseRepository


class ScoreRepository(BaseRepository[ScoreRecord]):
    @abstractmethod
    def get_current_score(self, politician_id: int) -> ScoreRecord | None:
        ...

    @abstractmethod
    def get_score_history(self, politician_id: int) -> list[ScoreRecord]:
        ...

    @abstractmethod
    def get_leaderboard(
        self,
        chamber: str | None = None,
        state: str | None = None,
        party: str | None = None,
        sort_by: str = "overall_score",
        offset: int = 0,
        limit: int = 20,
    ) -> list[tuple[int, ScoreRecord]]:
        """Returns list of (politician_id, score) tuples sorted by the given field."""
        ...

    @abstractmethod
    def count_leaderboard(
        self,
        chamber: str | None = None,
        state: str | None = None,
        party: str | None = None,
    ) -> int:
        """Count leaderboard entries matching the given filters."""
        ...

    @abstractmethod
    def get_scores_for_politicians(
        self, politician_ids: list[int]
    ) -> dict[int, ScoreRecord]:
        """Bulk fetch current scores keyed by politician_id."""
        ...

    @abstractmethod
    def bulk_create(self, records: list[ScoreRecord]) -> list[ScoreRecord]:
        ...

    @abstractmethod
    def invalidate_current_scores(self, politician_ids: list[int]) -> int:
        """Mark existing current scores as non-current. Returns count updated."""
        ...
