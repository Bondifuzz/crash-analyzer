from __future__ import annotations
from typing import TYPE_CHECKING

from ..util import PydanticBaseModel
from typing import Optional

import logging


class ORMBase(PydanticBaseModel):
    def __init__(self, **data):
        if not __debug__:
            name = self.__class__.__name__
            logging.warning(f"{name}: Using constructor instead of from_XXX() method")
        super().__init__(**data)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data) if __debug__ else cls.construct(**data)

    @classmethod
    def from_kwargs(cls, **data):
        return cls(**data) if __debug__ else cls.construct(**data)


class ORMCrashInfo(ORMBase):
    key: Optional[str]

    fuzzer_id: str
    fuzzer_rev: str

    input_hash: str
    unique_hash: str
    
