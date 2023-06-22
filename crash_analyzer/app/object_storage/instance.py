from __future__ import annotations
from typing import TYPE_CHECKING

from .storage import ObjectStorage

if TYPE_CHECKING:
    from crash_analyzer.app.settings import AppSettings
    from .abstract import IObjectStorage


async def s3_init(settings: AppSettings) -> IObjectStorage:
    return await ObjectStorage.create(settings)
