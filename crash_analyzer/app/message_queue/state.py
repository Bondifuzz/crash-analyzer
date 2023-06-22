from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crash_analyzer.app.settings import AppSettings
    from crash_analyzer.app.message_queue.instance import Producers
    from crash_analyzer.app.database.abstract import IDatabase
    from crash_analyzer.app.object_storage.abstract import IObjectStorage


class MQAppState:
    producers: Producers
    db: IDatabase
    s3: IObjectStorage
    settings: AppSettings
