from __future__ import annotations
from typing import Optional, Tuple
from hashlib import sha256

import re
from crash_analyzer.app.util import find_end
from crash_analyzer.app.models import EngineID, LangID, LibfuzzerCrash


def truncate_llvm_log(text: str) -> str:
    run_pos = find_end(text, "Running: ")
    if run_pos == -1:
        start = 0
    else:
        start = find_end(text, "\n", run_pos)
    
    sum_pos = find_end(text, "SUMMARY: ", start)
    if sum_pos == -1:
        return ""
    else:
        end = find_end(text, "\n", sum_pos)

    text = text[start:end]
    return text

# TODO: debug jazzer and swift output
def parse_crash(engine: EngineID, lang: LangID, crash_dict: dict) -> Tuple[Optional[str], str]:

    if engine not in {
        EngineID.libfuzzer,
        EngineID.jazzer, # TODO: remove todo when brief done
        EngineID.atheris,
        EngineID.cargo_fuzz,
        EngineID.go_fuzz_libfuzzer,
    }:
        raise NotImplementedError(f'Not implemented engine {engine} for libfuzzer!')

    crash = LibfuzzerCrash(**crash_dict)
    stacktrace = _read_stacktrace(crash.output, engine, lang)
    brief = _read_brief(stacktrace, engine, lang)

    if engine == EngineID.atheris:
        stacktrace = _clean_atheris_output(stacktrace)
    else:
        stacktrace = _clean_generic_output(stacktrace)

    stacktrace_hash = sha256(stacktrace.encode()).hexdigest()
    return brief, stacktrace_hash


def _clean_generic_output(output: str) -> str:
    tc_null = "==??=="
    hex_null = "0x??"
    dec_null = "??"
    thread_null = "thread T?"

    # TODO: re.compile?
    cleaned = truncate_llvm_log(output)
    cleaned = re.sub(r"==\d+==", tc_null, cleaned, flags=re.IGNORECASE) # remove ==X==
    cleaned = re.sub(r"([^\w+])0x[0-9a-f]+", r"\g<1>" + hex_null, cleaned, flags=re.IGNORECASE) # remove hex numbers
    cleaned = re.sub(r"(\s)(?!0x)\d+", r"\g<1>" + dec_null, cleaned, flags=re.IGNORECASE) # remove decimal numbers
    cleaned = re.sub(r"thread T\d+", thread_null, cleaned, flags=re.IGNORECASE) # remove T0

    return cleaned


clean_numbers = re.compile(r"0x[0-9a-f]+|[0-9]+")

"""

 === Uncaught Python exception: ===
ZeroDivisionError: division by zero
Traceback (most recent call last):
  File "/home/stalker7779/test-samples/libfuzz/python/divzero/src/./divzero-fuzzer.py", line 15, in TestOneInput
    c = a / (b - 30)

"""
def _clean_atheris_output(text: str) -> str:

    def _clean(line: str) -> str:
        # "  File "/some/path.py", line 15, in TestOneInput"
        # "    c = a / (b - 30)"
        if line.startswith(" "):
            return line

        else:
            return clean_numbers.sub("", line)

    return "\n".join(map(_clean, text.splitlines()))


def _read_brief(stacktrace: str, engine: EngineID, lang: LangID) -> Optional[str]:
    match = None
    if engine == EngineID.go_fuzz_libfuzzer:
        """
            panic: runtime error: integer divide by zero
            panic: kek
        """
        match = re.search(r"^panic: (.+)$", stacktrace, re.MULTILINE)
    
    elif engine == EngineID.cargo_fuzz:
        """
            writeln!(err, "thread '{name}' panicked at '{msg}', {location}");
            thread '<unnamed>' panicked at 'attempt to subtract with overflow', src/main.rs:10:21
        """
        match = re.search(r"^thread '.+' panicked at '(.+)', ", stacktrace, re.MULTILINE)

    elif engine == EngineID.atheris:
        """
            === Uncaught Python exception: ===
            ZeroDivisionError: division by zero
            Traceback (most recent call last):
        """
        match = re.search(
            r"=== Uncaught Python exception: ===\s+" # === Uncaught Python exception: ===
            r"([^\r\n]+)\s+"                         # ZeroDivisionError: division by zero
            r"Traceback \(most recent call last\):", # Traceback (most recent call last):
            stacktrace,
            re.MULTILINE
        )

    elif engine == EngineID.jazzer:
        """
            == Java Exception: java.lang.ArithmeticException: / by zero
        """
        match = re.search(r"^== Java Exception: (.+)$", stacktrace, re.MULTILINE)

    if match is None:
        match = re.search(r"^SUMMARY: (.+)$", stacktrace, re.MULTILINE)

    if match is not None:
        return match[1].strip()
    
    return None


def _read_stacktrace(output: str, engine: EngineID, lang: LangID) -> str:
    if engine == EngineID.libfuzzer:
        return _read_libfuzzer_stacktrace(output)
    if engine == EngineID.go_fuzz_libfuzzer:
        return _read_go_fuzz_stacktrace(output)
    if engine == EngineID.cargo_fuzz:
        return _read_cargo_fuzz_stacktrace(output)
    if engine == EngineID.atheris:
        return _read_atheris_stacktrace(output)
    if engine == EngineID.jazzer:
        return _read_jazzer_stacktrace(output)

    raise NotImplementedError(f"Unknown engine: {engine}")


def _read_libfuzzer_stacktrace(output: str):
    header_re = re.compile(r"^==[0-9]+==ERROR: .*$")
    in_stacktrace = False
    res = []
    for line in output.splitlines(True):
        if not in_stacktrace:
            if header_re.match(line):
                in_stacktrace = True
                res.append(line)
        else:
            res.append(line)
            if line.startswith("SUMMARY: "):
                break

    return "\n".join(res)


def _read_jazzer_stacktrace(output: str):
    header_re = re.compile(r"^== Java Exception: .*$")
    in_stacktrace = False
    res = []
    for line in output.splitlines(True):
        if not in_stacktrace:
            if header_re.match(line):
                in_stacktrace = True
                res.append(line)
        else:
            if line.startswith("DEDUP_TOKEN:"): # or line.startswith("== ")
                break
            res.append(line)
    
    return "\n".join(res)


def _read_cargo_fuzz_stacktrace(output: str):
    header_re = re.compile(r"^thread '.*' panicked at '.*', .*$")
    in_stacktrace = False
    res = []
    for line in output.splitlines(True):
        if not in_stacktrace:
            if header_re.match(line):
                in_stacktrace = True
                res.append(line)
        else:
            if '=========' in line or '== ERROR: ' in line:
                break
            res.append(line)
    
    return "\n".join(res)


def _read_atheris_stacktrace(output: str):
    header_re = re.compile(r"^\s*=== Uncaught Python exception: ===$")
    in_stacktrace = False
    res = []
    for line in output.splitlines(True):
        if not in_stacktrace:
            if header_re.match(line):
                in_stacktrace = True
                res.append(line)
        else:
            if '=========' in line or '== ERROR: ' in line:
                break
            res.append(line)

    return "\n".join(res)


def _read_go_fuzz_stacktrace(output: str):
    res = []
    for line in output.splitlines(True):
        if line.startswith("panic: "):
            res = [line]
        else:
            res.append(line)

    for i in range(len(res)):
        if '=========' in res[i] or '== ERROR: ' in res[i]:
            res = res[0:i]
            break

    return "\n".join(res)
