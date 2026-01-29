from __future__ import annotations

import os
import time
from typing import Any


def _try_import_psutil():
    try:
        import psutil  # type: ignore
    except Exception:
        return None
    return psutil


def _get_load_1m() -> float:
    # Cross-platform: os.getloadavg is Unix-only.
    try:
        if hasattr(os, "getloadavg"):
            return float(os.getloadavg()[0])
    except Exception:
        pass
    return 0.0


def _get_cpu_metrics(psutil_mod) -> dict[str, float]:
    # Keep fast: interval=0.0 returns immediately.
    # If psutil is absent or call fails, return numeric defaults.
    if psutil_mod is None:
        return {"user": 0.0, "total": 0.0}

    try:
        times = psutil_mod.cpu_times_percent(interval=0.0)
        user = float(getattr(times, "user", 0.0))
        # total as "busy" percentage (100 - idle), clamp into [0, 100]
        idle = float(getattr(times, "idle", 0.0))
        total = 100.0 - idle
        if total < 0.0:
            total = 0.0
        if total > 100.0:
            total = 100.0
        return {"user": user, "total": float(total)}
    except Exception:
        return {"user": 0.0, "total": 0.0}


def _get_mem_metrics(psutil_mod) -> dict[str, float]:
    # mem.used in bytes; if unavailable, return 0.0 numeric.
    if psutil_mod is None:
        return {"used": 0.0}

    try:
        vm = psutil_mod.virtual_memory()
        used = float(getattr(vm, "used", 0.0))
        return {"used": used}
    except Exception:
        return {"used": 0.0}


def get_metrics() -> dict[str, Any]:
    """
    Returns a snapshot dict with keys:
      - now: float epoch seconds
      - cpu: {"user": float, "total": float}
      - mem: {"used": float}   (bytes)
      - load: float            (1-minute loadavg; 0.0 if unsupported)
    """
    psutil_mod = _try_import_psutil()

    now = float(time.time())
    cpu = _get_cpu_metrics(psutil_mod)
    mem = _get_mem_metrics(psutil_mod)
    load = _get_load_1m()

    return {
        "now": now,
        "cpu": cpu,
        "mem": mem,
        "load": float(load),
    }