from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Optional

from abc import abstractmethod, ABCMeta
from ..util import testing_only

if TYPE_CHECKING:
    from ..settings import AppSettings
    from .orm import ORMCrashInfo


class IDBCrashIterator(metaclass=ABCMeta):
    @abstractmethod
    def __aiter__(self) -> IDBCrashIterator:
        pass

    @abstractmethod
    async def __anext__(self) -> ORMCrashInfo:
        pass


class ICrashes(metaclass=ABCMeta):
    @abstractmethod
    async def get(self, key: str) -> Optional[ORMCrashInfo]:
        pass

    @abstractmethod
    async def get_by_hash(
        self,
        fuzzer_id: str,
        fuzzer_rev: str,
        unique_hash: str,
    ) -> Optional[ORMCrashInfo]:
        pass

    @abstractmethod
    async def insert(self, crash: ORMCrashInfo) -> None:
        pass

    @abstractmethod
    async def update(self, crash: ORMCrashInfo) -> None:
        pass

    @abstractmethod
    async def get_revision_crashes(
        self, fuzzer_id: str, revision: str
    ) -> IDBCrashIterator:
        pass

class IUnsentMessages(metaclass=ABCMeta):

    """
    Used for saving/loading MQ unsent messages from database.
    """

    @abstractmethod
    async def save_unsent_messages(self, messages: Dict[str, list]):
        pass

    @abstractmethod
    async def load_unsent_messages(self) -> Dict[str, list]:
        pass

class IDatabase(metaclass=ABCMeta):

    """Used for managing database"""

    @classmethod
    @abstractmethod
    async def create(cls, settings: AppSettings):
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    @property
    @abstractmethod
    def crashes(self) -> ICrashes:
        pass

    @property
    @abstractmethod
    def unsent_mq(self) -> IUnsentMessages:
        pass

    @abstractmethod
    @testing_only
    async def truncate_all_collections(self) -> None:
        pass
