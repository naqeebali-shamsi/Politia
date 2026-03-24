from abc import abstractmethod

from app.domain.entities.activity import ActivityRecord
from app.domain.interfaces.base_repository import BaseRepository


class ActivityRepository(BaseRepository[ActivityRecord]):
    @abstractmethod
    def get_by_politician(
        self, politician_id: int, term_number: int | None = None
    ) -> list[ActivityRecord]:
        ...

    @abstractmethod
    def get_chamber_averages(
        self, term_number: int | None = None
    ) -> dict[str, float]:
        """Returns average attendance, questions, debates across the chamber for normalization."""
        ...

    @abstractmethod
    def bulk_create(self, records: list[ActivityRecord]) -> list[ActivityRecord]:
        ...
