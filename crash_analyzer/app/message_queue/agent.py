from __future__ import annotations
from typing import TYPE_CHECKING, Tuple

from crash_analyzer.app.models import CrashBase, LangID, EngineID
from crash_analyzer.app.database.orm import ORMCrashInfo

from mqtransport.participants import Consumer
from pydantic import BaseModel, validator
from typing import Optional

import base64
from hashlib import sha256

import crash_analyzer.app.agents.libfuzzer as libfuzzer
import crash_analyzer.app.agents.afl as afl

if TYPE_CHECKING:
    from mqtransport import MQApp
    from crash_analyzer.app.message_queue.state import MQAppState


class MC_NewCrash(Consumer):
    name: str = "agent.crash.new"

    class Model(BaseModel):
        user_id: str
        """ Id of user which owns pool and project in which fuzzer ran """

        project_id: str
        """ Id of project in which fuzzer ran """

        pool_id: str
        """ Id of pool in which fuzzer ran """

        fuzzer_id: str
        """ Id of fuzzer which crash belongs to """

        fuzzer_rev: str
        """ Id of revision which crash belongs to """

        fuzzer_engine: EngineID
        """ Fuzzing engine which crash belongs to """

        fuzzer_lang: LangID
        """ Language of fuzzer which crash belongs to """

        crash: dict
        """ Crash info """

        created: str
        """ Time, when crash found(rfc3339) """

    @validator("created", pre=True)
    def validate_time(cls, value: str):
        if not value.endswith("Z"):
            raise ValueError("Not a valid rfc3339 time")
        return value

    async def consume(self, msg: Model, app: MQApp):
        state: MQAppState = app.state
        settings = state.settings.crash_analyzer
        crash_base = CrashBase(**msg.crash)

        input_data = await self.get_input_data(
            state=state,
            fuzzer_id=msg.fuzzer_id,
            fuzzer_rev=msg.fuzzer_rev,
            crash_base=crash_base,
        )
        input_hash = sha256(input_data).hexdigest()
        brief = None
        duplicate_of = None
        unique_hash = None

        if crash_base.reproduced:
            (duplicate_of, brief, unique_hash) = await self.handle_crash(
                msg, app, input_hash
            )
        
        if brief is None:
            brief = f"{crash_base.type}: UNKNOWN"

        # unique crash
        if duplicate_of is None:
            self._logger.info(f"Found unique crash brief: {brief}, unique_hash: {unique_hash}")
            preview = input_data
            if len(preview) > settings.preview_max_size:
                preview = preview[:settings.preview_max_size]

            await state.producers.unique_crash.produce(
                created=msg.created,
                fuzzer_id=msg.fuzzer_id,
                fuzzer_rev=msg.fuzzer_rev,
                preview=base64.b64encode(preview).decode(),
                input_id=crash_base.input_id,
                input_hash=input_hash, # TODO:
                output=crash_base.output,
                brief=brief,
                reproduced=crash_base.reproduced,
                type=crash_base.type,
            )

        # duplicate
        else:
            self._logger.info(f"Found duplicate crash brief: {brief}, unique_hash: {unique_hash}")
            await state.producers.duplicated_crash.produce(
                fuzzer_id=msg.fuzzer_id,
                fuzzer_rev=msg.fuzzer_rev,
                input_hash=duplicate_of.input_hash, # TODO:
            )

    async def handle_crash(self, msg: Model, app: MQApp, input_hash: str) -> Tuple[Optional[ORMCrashInfo], Optional[str], str]:
        state: MQAppState = app.state
        
        if EngineID.is_libfuzzer(msg.fuzzer_engine):
            brief, unique_hash = libfuzzer.parse_crash(
                msg.fuzzer_engine,
                msg.fuzzer_lang,
                msg.crash,
            )

        elif EngineID.is_afl(msg.fuzzer_engine):
            brief, unique_hash = afl.parse_crash(
                msg.fuzzer_engine,
                msg.fuzzer_lang,
                msg.crash,
            )

        else:
            raise NotImplementedError(
                f"Unknown fuzzer engine: {msg.fuzzer_engine}"
            )

        duplicate_of = await state.db.crashes.get_by_hash(
            fuzzer_id=msg.fuzzer_id,
            fuzzer_rev=msg.fuzzer_rev,
            unique_hash=unique_hash,
        )
            
        if duplicate_of is None:
            await state.db.crashes.insert(
                ORMCrashInfo(
                    fuzzer_id=msg.fuzzer_id,
                    fuzzer_rev=msg.fuzzer_rev,
                    input_hash=input_hash,
                    unique_hash=unique_hash,
                )
            )
        
        return (duplicate_of, brief, unique_hash)


    async def get_input_data(self, state: MQAppState, fuzzer_id: str, fuzzer_rev: str, crash_base: CrashBase) -> bytes:
        if crash_base.input is not None:
            return base64.b64decode(crash_base.input)
        
        else:
            data = b''

            stream = await state.s3.download_crash(
                fuzzer_id, fuzzer_rev, crash_base.input_id
            )
            async for chunk in stream:
                data += chunk
            return data
