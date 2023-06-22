from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from mqtransport.participants import Producer
from pydantic import BaseModel, validator

if TYPE_CHECKING:
    pass

class MP_UniqueCrashFound(Producer):
    name: str = "crash-analyzer.crashes.unique"

    class Model(BaseModel):

        created: str
        """ Date when crash was retrieved """

        fuzzer_id: str
        """ Id of fuzzer which crash belongs to """

        fuzzer_rev: str
        """ Id of revision which crash belongs to """

        preview: str
        """ Chunk of crash input to preview (base64-encoded) """

        input_id: Optional[str]
        """ Identifies crash info in object storage """

        input_hash: str
        """ Unique hash of crash input """

        output: str
        """ Crash output (long multiline text) """

        brief: str
        """ Short description for crash """

        reproduced: bool
        """ True if crash was reproduced, else otherwise """

        type: str
        """ Type of crash """

        @validator("created", pre=True)
        def validate_time(cls, value: str):
            if not value.endswith("Z"):
                raise ValueError("Not a valid rfc3339 time")
            return value


class MP_DuplicateCrashFound(Producer):
    name: str = "crash-analyzer.crashes.duplicate"

    class Model(BaseModel):
        fuzzer_id: str
        """ Id of fuzzer which crash belongs to """

        fuzzer_rev: str
        """ Id of revision which crash belongs to """

        input_hash: str
        """ Unique hash of crash input """