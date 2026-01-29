import os
import re
import shlex
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text)


def quote_string(s: str) -> str:
    # Basic quoting compatible with shlex parsing expectations
    if s == "":
        return "''"
    if re.search(r"\s|[\\\"']", s):
        return shlex.quote(s)
    return s


def is_text_file(path: str) -> bool:
    # Very small heuristic; used for transcript reading.
    try:
        with open(path, "rb") as f:
            chunk = f.read(4096)
        if b"\x00" in chunk:
            return False
        return True
    except OSError:
        return False


def norm_line_endings(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def ensure_list(val: Optional[Sequence[str]]) -> List[str]:
    if val is None:
        return []
    return list(val)


@dataclass
class ProcResult:
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0


def which(program: str) -> Optional[str]:
    # Simple shutil.which alternative without importing shutil
    paths = os.environ.get("PATH", "").split(os.pathsep)
    exts: Iterable[str]
    if os.name == "nt":
        pathext = os.environ.get("PATHEXT", ".EXE;.BAT;.CMD")
        exts = [e.lower() for e in pathext.split(";") if e]
    else:
        exts = [""]

    for p in paths:
        if not p:
            continue
        for ext in exts:
            cand = os.path.join(p, program + ext)
            if os.path.isfile(cand) and os.access(cand, os.X_OK):
                return cand
    return None


def smart_environ_get(key: str, default: str = "") -> str:
    try:
        return os.environ.get(key, default)
    except Exception:
        return default


def stderr_print(*args, **kwargs) -> None:
    kwargs.setdefault("file", sys.stderr)
    print(*args, **kwargs)