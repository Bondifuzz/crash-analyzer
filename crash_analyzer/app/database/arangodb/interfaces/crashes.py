from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from crash_analyzer.app.database.arangodb.interfaces.base import DBBase
from crash_analyzer.app.database.orm import ORMCrashInfo
from crash_analyzer.app.database.abstract import ICrashes, IDBCrashIterator
from .util import (
    maybe_already_exists,
    maybe_not_found,
    maybe_unknown_error,
)

if TYPE_CHECKING:
    from aioarangodb.collection import StandardCollection
    from crash_analyzer.app.settings import CollectionSettings
    from crash_analyzer.app.database.arangodb.database import ArangoDB
    from aioarangodb.cursor import Cursor


class DBArangoCrashIterator(IDBCrashIterator):
    _cursor: Cursor

    def __init__(self, cursor: Cursor):
        self._cursor = cursor

    def __aiter__(self) -> IDBCrashIterator:
        return self

    async def __anext__(self) -> ORMCrashInfo:
        doc = await self._cursor.__anext__()  # raise StopAsyncIteration()
        doc["key"] = doc["_key"]
        return ORMCrashInfo.from_dict(doc)


class DBCrashes(DBBase, ICrashes):

    _col_crashes: StandardCollection

    def __init__(
        self,
        db: ArangoDB,
        collections: CollectionSettings,
    ):
        self._col_crashes = db._db[collections.crashes]
        super().__init__(db, collections)

    @maybe_unknown_error
    async def get(self, key: str) -> Optional[ORMCrashInfo]:
        crash_dict = await self._col_crashes.get(key)
        if crash_dict is None:
            return None
        crash_dict["key"] = crash_dict["_key"]
        return ORMCrashInfo.from_dict(crash_dict)

    @maybe_unknown_error
    async def get_by_hash(
        self,
        fuzzer_id: str,
        fuzzer_rev: str,
        unique_hash: str,
    ) -> Optional[ORMCrashInfo]:

        filters = {
            "fuzzer_id": fuzzer_id,
            "fuzzer_rev": fuzzer_rev,
            "unique_hash": unique_hash,
        }
        cursor: Cursor = await self._col_crashes.find(filters, limit=1)

        if cursor.empty():
            return None
        crash_dict = cursor.pop()
        crash_dict["key"] = crash_dict["_key"]
        return ORMCrashInfo(**crash_dict)

    @maybe_unknown_error
    async def insert(self, crash: ORMCrashInfo) -> None:
        res = await self._col_crashes.insert(crash.dict(exclude={"key"}))
        crash.key = res["_key"]

    @maybe_unknown_error
    async def update(self, crash: ORMCrashInfo) -> None:
        crash_dict = crash.dict(exclude={"key"})
        crash_dict["_key"] = crash.key
        await self._col_crashes.update(crash_dict)

    @maybe_unknown_error
    async def get_revision_crashes(
        self, fuzzer_id: str, revision: str
    ) -> IDBCrashIterator:
        cursor: Cursor = await self._col_crashes.find(
            {"fuzzer_id": fuzzer_id, "fuzzer_rev": revision}
        )
        return DBArangoCrashIterator(cursor)
