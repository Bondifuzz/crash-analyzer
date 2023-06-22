from typing import TYPE_CHECKING, Optional
from contextlib import AsyncExitStack
from asyncio import CancelledError
from typing import BinaryIO, Union
from io import BytesIO
import logging

from .abstract import IObjectStorage, IStreamingDownload
from .initializer import ObjectStorageInitializer
from .paths import BucketFuzzers, BucketData

from .errors import maybe_not_found, maybe_unknown_error
from .errors import UploadLimitError


if TYPE_CHECKING:
    from aioboto3_hints.s3.service_resource import ServiceResource as S3Resource
    from aioboto3_hints.s3.client import Client as S3Client
else:
    S3Resource = object
    S3Client = object


class UploadLimitTracker:

    _stream: BinaryIO
    _limit: int
    _total: int

    def __init__(self, stream: BinaryIO, limit: int):
        self._stream = stream
        self._limit = limit
        self._total = 0

    async def read(self, size: int = -1) -> Union[bytes, str]:

        bytes_read = await self._stream.read(size)

        self._total += len(bytes_read)
        if self._total > self._limit:
            raise UploadLimitError()

        return bytes_read

    def is_limit_reached(self):
        return self._total > self._limit


class StreamingDownload(IStreamingDownload):

    _chunk_size: int = 4096
    _stack: AsyncExitStack
    _stream: BinaryIO

    def __init__(self):
        self._stack = AsyncExitStack()
        self._stream = None

    @staticmethod
    async def create(s3_object):
        _self = StreamingDownload()
        await _self._init(s3_object)
        return _self

    async def _init(self, s3_object):
        self._stream = await self._stack.enter_async_context(s3_object["Body"])

    def __aiter__(self) -> IStreamingDownload:
        return self

    async def __anext__(self) -> bytes:

        data: bytes = await self._stream.read(self._chunk_size)

        if not data:
            await self._stack.aclose()
            raise StopAsyncIteration()

        return data


class ObjectStorage(IObjectStorage):

    _s3: S3Resource
    _client: S3Client
    _context_stack: Optional[AsyncExitStack]
    _logger: logging.Logger
    _is_closed: bool

    _bucket_fuzzers: BucketFuzzers
    _bucket_data: BucketData

    async def _init(self, settings):

        self._is_closed = True
        self._context_stack = None
        self._logger = logging.getLogger("s3")

        initializer = await ObjectStorageInitializer.create(settings)
        await initializer.do_init()

        self._s3 = initializer.s3
        self._client = initializer.s3.meta.client
        self._context_stack = initializer.context_stack
        self._bucket_fuzzers = initializer.bucket_fuzzers
        self._bucket_data = initializer.bucket_data
        self._is_closed = False

    @staticmethod
    async def create(settings):
        _self = ObjectStorage()
        await _self._init(settings)
        return _self

    async def close(self):

        assert not self._is_closed, "ObjectStorage connection has been already closed"

        if self._context_stack:
            await self._context_stack.aclose()
            self._context_stack = None

        self._is_closed = True

    def __del__(self):
        if not self._is_closed:
            self._logger.error("ObjectStorage connection has not been closed")

    @maybe_unknown_error
    async def _upload_file(
        self,
        stream: BinaryIO,
        bucket_name: str,
        object_key: str,
        upload_limit: int,
    ):
        assert upload_limit > 0
        tracker = UploadLimitTracker(stream, upload_limit)

        try:
            await self._client.upload_fileobj(tracker, bucket_name, object_key)
        except CancelledError:
            if tracker.is_limit_reached():
                raise UploadLimitError()
            raise

    @maybe_unknown_error
    async def _upload_text(
        self,
        text_encoded: bytes,
        bucket_name: str,
        object_key: str,
    ):
        stream = BytesIO(text_encoded)
        await self._client.upload_fileobj(stream, bucket_name, object_key)

    @maybe_unknown_error
    @maybe_not_found
    async def _download_file(
        self,
        bucket_name: str,
        object_key: str,
    ):
        obj = await self._client.get_object(Bucket=bucket_name, Key=object_key)
        return await StreamingDownload.create(obj)

    @maybe_unknown_error
    @maybe_not_found
    async def _download_text(
        self,
        bucket_name: str,
        object_key: str,
    ):
        stream = BytesIO()
        downloader = await self._download_file(bucket_name, object_key)

        async for chunk in downloader:
            stream.write(chunk)

        return stream.getvalue()

    async def upload_fuzzer_config(
        self,
        fuzzer_id: str,
        fuzzer_rev: str,
        config: bytes,
    ):
        bucket, key = self._bucket_fuzzers.config(fuzzer_id, fuzzer_rev)
        await self._upload_text(config, bucket, key)

    async def download_fuzzer_config(self, fuzzer_id: str, fuzzer_rev: str) -> dict:
        bucket, key = self._bucket_fuzzers.config(fuzzer_id, fuzzer_rev)
        return await self._download_text(bucket, key)

    async def upload_fuzzer_binaries(
        self,
        fuzzer_id: str,
        fuzzer_rev: str,
        stream: BinaryIO,
        upload_limit: int = 0,
    ):
        bucket, key = self._bucket_fuzzers.binaries(fuzzer_id, fuzzer_rev)
        await self._upload_file(stream, bucket, key, upload_limit)

    async def download_fuzzer_binaries(self, fuzzer_id: str, fuzzer_rev: str):
        bucket, key = self._bucket_fuzzers.binaries(fuzzer_id, fuzzer_rev)
        return await self._download_file(bucket, key)

    async def upload_fuzzer_seeds(
        self,
        fuzzer_id: str,
        fuzzer_rev: str,
        stream: BinaryIO,
        upload_limit: int = 0,
    ):
        bucket, key = self._bucket_fuzzers.seeds(fuzzer_id, fuzzer_rev)
        await self._upload_file(stream, bucket, key, upload_limit)

    async def download_fuzzer_seeds(self, fuzzer_id: str, fuzzer_rev: str):
        bucket, key = self._bucket_fuzzers.seeds(fuzzer_id, fuzzer_rev)
        return await self._download_file(bucket, key)

    async def download_crash(
        self, fuzzer_id: str, fuzzer_rev: str, crash_id: str
    ) -> IStreamingDownload:
        bucket, key = self._bucket_data.crash(fuzzer_id, fuzzer_rev, crash_id)
        return await self._download_file(bucket, key)
