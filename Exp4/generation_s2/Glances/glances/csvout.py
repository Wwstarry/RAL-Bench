from __future__ import annotations

import time
from typing import Callable, Dict, List

import psutil

from .exceptions import UnknownFieldError


def _now() -> str:
    # Epoch seconds with fractional part; numeric and parseable.
    return f"{time.time():.6f}"


def _cpu_user() -> str:
    # user percentage over a very short interval; numeric parseable.
    # interval=0.0 gives last computed value; first call may be 0.0 which is fine.
    v = psutil.cpu_times_percent(interval=0.0).user
    return f"{float(v):.2f}"


def _cpu_total() -> str:
    # total busy percentage: 100 - idle
    v = 100.0 - float(psutil.cpu_times_percent(interval=0.0).idle)
    # Clamp for safety
    if v < 0.0:
        v = 0.0
    elif v > 100.0:
        v = 100.0
    return f"{v:.2f}"


def _mem_used() -> str:
    # bytes used
    v = int(psutil.virtual_memory().used)
    return str(v)


def _load() -> str:
    # 1-minute load average if available; else approximate with normalized CPU percent.
    try:
        la1, _, _ = psutil.getloadavg()  # may raise AttributeError/OSError on some platforms
        return f"{float(la1):.2f}"
    except Exception:
        # Approximation: CPU percent (0-100) scaled to cores -> "load-like"
        try:
            pct = float(psutil.cpu_percent(interval=0.0))
        except Exception:
            pct = 0.0
        cores = psutil.cpu_count() or 1
        load_like = (pct / 100.0) * cores
        return f"{load_like:.2f}"


_FIELD_FUNCS: Dict[str, Callable[[], str]] = {
    "now": _now,
    "cpu.user": _cpu_user,
    "cpu.total": _cpu_total,
    "mem.used": _mem_used,
    "load": _load,
}


def _parse_fields(fields: str) -> List[str]:
    items = [f.strip() for f in (fields or "").split(",")]
    items = [f for f in items if f]
    return items


def csv_one_shot(fields: str) -> str:
    req = _parse_fields(fields)
    if not req:
        raise UnknownFieldError("error: --stdout-csv requires at least one field")

    unknown = [f for f in req if f not in _FIELD_FUNCS]
    if unknown:
        raise UnknownFieldError("error: unknown field(s): " + ", ".join(unknown))

    # Compute values in requested order.
    vals = [_FIELD_FUNCS[f]() for f in req]
    return ",".join(vals)