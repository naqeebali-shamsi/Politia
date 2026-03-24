from abc import abstractmethod

from app.domain.entities.source import SourceRecord
from app.domain.interfaces.base_repository import BaseRepository


class SourceRepository(BaseRepository[SourceRecord]):
    @abstractmethod
    def get_by_url(self, url: str) -> SourceRecord | None:
        ...

    @abstractmethod
    def get_by_checksum(self, checksum: str) -> SourceRecord | None:
        ...

    @abstractmethod
    def get_failed(self, limit: int = 100) -> list[SourceRecord]:
        ...

    @abstractmethod
    def bulk_create(self, records: list[SourceRecord]) -> list[SourceRecord]:
        ...
