from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crash_analyzer.app.settings import CollectionSettings
    from crash_analyzer.app.database.arangodb.database import ArangoDB


class DBBase:

    _db: ArangoDB
    _collections: CollectionSettings

    def __init__(self, db: ArangoDB, collections: CollectionSettings):
        self._collections = collections
        self._db = db
