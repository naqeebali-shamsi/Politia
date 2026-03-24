from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    def get_by_id(self, entity_id: int) -> T | None:
        ...

    @abstractmethod
    def get_all(self, offset: int = 0, limit: int = 20) -> list[T]:
        ...

    @abstractmethod
    def create(self, entity: T) -> T:
        ...

    @abstractmethod
    def update(self, entity: T) -> T:
        ...

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        ...

    @abstractmethod
    def count(self) -> int:
        ...
