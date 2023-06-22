from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, root_validator


class StrEnum(str, Enum):
    """Enum where members are also (and must be) strs"""

class EngineID(StrEnum):
    # afl binding
    afl = "afl"
    afl_rs = "afl.rs"
    sharpfuzz_afl = "sharpfuzz-afl"

    # libfuzzer binding
    libfuzzer = "libfuzzer"
    jazzer = "jazzer"
    atheris = "atheris"
    cargo_fuzz = "cargo-fuzz"
    go_fuzz_libfuzzer = "go-fuzz-libfuzzer"
    sharpfuzz_libfuzzer = "sharpfuzz-libfuzzer"

    @staticmethod
    def is_afl(engine_id: EngineID):
        return engine_id in {
            EngineID.afl,
            EngineID.afl_rs,
            EngineID.sharpfuzz_afl,
        }

    @staticmethod
    def is_libfuzzer(engine_id: EngineID):
        return engine_id in {
            EngineID.libfuzzer,
            EngineID.jazzer,
            EngineID.atheris,
            EngineID.cargo_fuzz,
            EngineID.go_fuzz_libfuzzer,
            EngineID.sharpfuzz_libfuzzer,
        }


class LangID(StrEnum):
    go = "go" # go-fuzz-libfuzzer
    cpp = "cpp" # afl, libfuzzer
    rust = "rust" # afl.rs, cargo-fuzz
    java = "java" # jqf, jazzer
    swift = "swift" # libfuzzer
    python = "python" # atheris
    # javascript = "javascript" # libfuzzer


class CrashType(StrEnum):
    Crash = "crash"
    OOM = "oom"
    Timeout = "timeout"


class CrashBase(BaseModel):

    type: str
    """ Type of crash: crash, oom, timeout, leak, etc.. """

    input_id: Optional[str]
    """ Id (key) of uploaded to object storage input which caused program to abort """

    input: Optional[str]
    """ Crash input (base64-encoded). Used if crash file is not too large """

    output: str
    """ Crash output (long multiline text) """

    reproduced: bool
    """ True if crash was reproduced, else otherwise """

    @root_validator
    def input_id_or_input(cls, data: dict):

        if isinstance(data["input_id"], str):
            if len(data["input_id"]) > 0:
                return data

        if isinstance(data["input"], str):
            return data

        raise ValueError("input_id or input must be set")


class LibfuzzerCrash(CrashBase):
    pass


class AflCrash(CrashBase):
    showmap_hash: str
