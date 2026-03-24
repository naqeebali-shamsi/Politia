from abc import abstractmethod

from app.domain.entities.election import ElectionRecord
from app.domain.interfaces.base_repository import BaseRepository


class ElectionRepository(BaseRepository[ElectionRecord]):
    @abstractmethod
    def get_by_politician(self, politician_id: int) -> list[ElectionRecord]:
        ...

    @abstractmethod
    def get_by_constituency(
        self, constituency_id: int, year: int | None = None
    ) -> list[ElectionRecord]:
        ...

    @abstractmethod
    def bulk_create(self, records: list[ElectionRecord]) -> list[ElectionRecord]:
        ...
