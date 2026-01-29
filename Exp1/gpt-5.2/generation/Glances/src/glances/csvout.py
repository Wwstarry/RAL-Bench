from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Dict, List

from .metrics import (
    cpu_total_percent,
    cpu_user_percent,
    load_one,
    mem_used_bytes,
)


@dataclass(frozen=True)
class Field:
    name: str
    getter: Callable[[], str]


def _now_str() -> str:
    # Numeric-ish; tests may treat it as opaque for "now", but keep it stable and parseable.
    return str(time.time())


def _float_str(x: float) -> str:
    # Avoid locale issues; keep concise.
    if x != x:  # NaN
        return "nan"
    return f"{x:.6f}".rstrip("0").rstrip(".") if abs(x) < 1e12 else str(x)


def _int_str(x: int) -> str:
    return str(int(x))


_FIELDS: Dict[str, Field] = {
    "now": Field("now", _now_str),
    "cpu.user": Field("cpu.user", lambda: _float_str(cpu_user_percent())),
    "cpu.total": Field("cpu.total", lambda: _float_str(cpu_total_percent())),
    "mem.used": Field("mem.used", lambda: _int_str(mem_used_bytes())),
    "load": Field("load", lambda: _float_str(load_one())),
}


def stdout_csv_one_shot(fields_spec: str) -> str:
    if fields_spec is None:
        raise ValueError("--stdout-csv requires an argument")

    raw = [f.strip() for f in fields_spec.split(",")]
    fields = [f for f in raw if f != ""]
    if not fields:
        raise ValueError("no fields specified for --stdout-csv")

    unknown = [f for f in fields if f not in _FIELDS]
    if unknown:
        raise ValueError("unknown field(s): " + ", ".join(unknown))

    # Collect values in order. One-shot should be quick; avoid heavy sampling.
    out: List[str] = []
    for f in fields:
        out.append(_FIELDS[f].getter())
    return ",".join(out)