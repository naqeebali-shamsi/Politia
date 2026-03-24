from abc import abstractmethod

from app.domain.entities.disclosure import DisclosureRecord
from app.domain.interfaces.base_repository import BaseRepository


class DisclosureRepository(BaseRepository[DisclosureRecord]):
    @abstractmethod
    def get_by_politician(self, politician_id: int) -> list[DisclosureRecord]:
        ...

    @abstractmethod
    def get_latest_by_politician(self, politician_id: int) -> DisclosureRecord | None:
        ...

    @abstractmethod
    def bulk_create(self, records: list[DisclosureRecord]) -> list[DisclosureRecord]:
        ...
