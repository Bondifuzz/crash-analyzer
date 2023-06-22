from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import BinaryIO, Optional


class IStreamingDownload(metaclass=ABCMeta):

    """File streaming download"""

    @abstractmethod
    def __aiter__(self) -> IStreamingDownload:
        pass

    @abstractmethod
    async def __anext__(self) -> bytes:
        pass


class IObjectStorage(metaclass=ABCMeta):

    """Describes object storage operations"""

    @abstractmethod
    async def upload_fuzzer_config(
        self,
        fuzzer_id: str,
        fuzzer_rev: str,
        config_encoded: bytes,
    ):
        pass

    @abstractmethod
    async def download_fuzzer_config(self, fuzzer_id: str, fuzzer_rev: str) -> bytes:
        pass

    @abstractmethod
    async def upload_fuzzer_binaries(
        self,
        fuzzer_id: str,
        fuzzer_rev: str,
        stream: BinaryIO,
        upload_limit: int = 0,
    ):
        pass

    @abstractmethod
    async def download_fuzzer_binaries(
        self, fuzzer_id: str, fuzzer_rev: str
    ) -> IStreamingDownload:
        pass

    @abstractmethod
    async def upload_fuzzer_seeds(
        self,
        fuzzer_id: str,
        fuzzer_rev: str,
        stream: BinaryIO,
        upload_limit: int = 0,
    ):
        pass

    @abstractmethod
    async def download_fuzzer_seeds(
        self, fuzzer_id: str, fuzzer_rev: str
    ) -> IStreamingDownload:
        pass

    @abstractmethod
    async def download_crash(
        self, fuzzer_id: str, fuzzer_rev: str, crash_id: str
    ) -> IStreamingDownload:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
