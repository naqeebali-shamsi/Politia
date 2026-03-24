from abc import abstractmethod

from app.domain.entities.politician import Politician
from app.domain.interfaces.base_repository import BaseRepository


class PoliticianRepository(BaseRepository[Politician]):
    @abstractmethod
    def search(
        self,
        query: str = "",
        state: str | None = None,
        party: str | None = None,
        chamber: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Politician]:
        ...

    @abstractmethod
    def get_by_name(self, name: str) -> list[Politician]:
        ...

    @abstractmethod
    def get_by_constituency(self, constituency_id: int) -> list[Politician]:
        ...

    @abstractmethod
    def get_by_external_id(
        self, source: str, external_id: str
    ) -> Politician | None:
        """Look up politician by cross-source identifier (tcpd_id, myneta_id, etc.)."""
        ...

    @abstractmethod
    def search_count(
        self,
        query: str = "",
        state: str | None = None,
        party: str | None = None,
        chamber: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        ...

    @abstractmethod
    def get_distinct_states(self) -> list[str]:
        ...

    @abstractmethod
    def get_distinct_parties(self) -> list[str]:
        ...

    @abstractmethod
    def get_by_ids(self, entity_ids: list[int]) -> dict[int, Politician]:
        """Bulk fetch politicians by IDs. Returns dict keyed by politician_id."""
        ...

    @abstractmethod
    def bulk_create(self, entities: list[Politician]) -> list[Politician]:
        ...
