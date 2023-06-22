from __future__ import annotations
from typing import Optional, Tuple
from crash_analyzer.app.models import AflCrash, LangID, EngineID


def parse_crash(engine: EngineID, lang: LangID, crash_dict: dict) -> Tuple[Optional[str], str]:
    crash = AflCrash(**crash_dict)
    return None, crash.showmap_hash
