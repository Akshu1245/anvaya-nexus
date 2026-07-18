from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal


class Repository(ABC):
    """Storage boundary implemented by SQLite now and Catalyst in M7."""

    @abstractmethod
    def health_check(self) -> Literal["ok"]:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def initialize(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def table_count(self, table: str) -> int:
        raise NotImplementedError
