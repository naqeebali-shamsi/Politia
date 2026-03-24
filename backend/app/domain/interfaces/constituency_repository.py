from abc import abstractmethod

from app.domain.entities.constituency import Constituency
from app.domain.interfaces.base_repository import BaseRepository


class ConstituencyRepository(BaseRepository[Constituency]):
    @abstractmethod
    def search(
        self,
        query: str = "",
        state: str | None = None,
        chamber: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Constituency]:
        ...

    @abstractmethod
    def get_by_name_and_state(self, name: str, state: str) -> Constituency | None:
        ...

    @abstractmethod
    def bulk_create(self, entities: list[Constituency]) -> list[Constituency]:
        ...
