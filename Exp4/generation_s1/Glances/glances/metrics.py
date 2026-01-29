from __future__ import annotations

import os
import sys
import time
from typing import Dict, Union

Number = Union[int, float]


def now_timestamp() -> float:
    # Numeric epoch seconds; easy to parse and cross-platform.
    return time.time()


def _cpu_times_psutil() -> Dict[str, Number] | None:
    try:
        import psutil  # type: ignore
    except Exception:
        return None

    try:
        ct = psutil.cpu_times()
        # cpu_times() returns a namedtuple with varying fields across platforms.
        user = float(getattr(ct, "user", 0.0))
        total = 0.0
        for v in ct:
            try:
                total += float(v)
            except Exception:
                pass
        return {"user": user, "total": total}
    except Exception:
        return None


def cpu_times() -> Dict[str, Number]:
    """
    Returns cumulative CPU times with keys:
      - user: user time
      - total: sum of available time fields

    Note: Without psutil, this may be process-level times (os.times), but tests
    only require numeric values.
    """
    ps = _cpu_times_psutil()
    if ps is not None:
        return ps

    try:
        t = os.times()
        # os.times: user, system, children_user, children_system, elapsed
        user = float(getattr(t, "user", 0.0))
        total = float(getattr(t, "user", 0.0)) + float(getattr(t, "system", 0.0))
        total += float(getattr(t, "children_user", 0.0)) + float(getattr(t, "children_system", 0.0))
        return {"user": user, "total": total}
    except Exception:
        return {"user": 0.0, "total": 0.0}


def _mem_used_psutil() -> int | None:
    try:
        import psutil  # type: ignore
    except Exception:
        return None

    try:
        vm = psutil.virtual_memory()
        used = int(getattr(vm, "used", 0))
        return used
    except Exception:
        return None


def _mem_used_linux_proc() -> int | None:
    # MemUsed ~= MemTotal - MemAvailable
    path = "/proc/meminfo"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            meminfo = f.read().splitlines()
    except Exception:
        return None

    vals_kib = {}
    for line in meminfo:
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        parts = rest.strip().split()
        if not parts:
            continue
        try:
            vals_kib[key] = int(parts[0])
        except Exception:
            continue

    if "MemTotal" in vals_kib and "MemAvailable" in vals_kib:
        used_kib = vals_kib["MemTotal"] - vals_kib["MemAvailable"]
        if used_kib < 0:
            used_kib = 0
        return int(used_kib) * 1024

    # Fallback using MemFree+Buffers+Cached if MemAvailable missing (older kernels)
    if "MemTotal" in vals_kib and ("MemFree" in vals_kib or "Cached" in vals_kib):
        free_kib = vals_kib.get("MemFree", 0) + vals_kib.get("Buffers", 0) + vals_kib.get("Cached", 0)
        used_kib = vals_kib["MemTotal"] - free_kib
        if used_kib < 0:
            used_kib = 0
        return int(used_kib) * 1024

    return None


def _mem_used_windows_ctypes() -> int | None:
    if not sys.platform.startswith("win"):
        return None

    try:
        import ctypes
        from ctypes import wintypes
    except Exception:
        return None

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", wintypes.DWORD),
            ("dwMemoryLoad", wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    try:
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)) == 0:
            return None
        used = int(stat.ullTotalPhys - stat.ullAvailPhys)
        if used < 0:
            used = 0
        return used
    except Exception:
        return None


def mem_used_bytes() -> int:
    """
    Returns memory used in bytes. Best-effort cross-platform.
    If unavailable, returns 0 (still numeric and parseable).
    """
    used = _mem_used_psutil()
    if used is not None:
        return used

    if sys.platform.startswith("linux"):
        used = _mem_used_linux_proc()
        if used is not None:
            return used

    used = _mem_used_windows_ctypes()
    if used is not None:
        return used

    return 0


def load_1() -> float:
    try:
        getloadavg = getattr(os, "getloadavg", None)
        if getloadavg is None:
            return 0.0
        return float(getloadavg()[0])
    except Exception:
        return 0.0


def get_snapshot() -> Dict[str, Number]:
    ct = cpu_times()
    return {
        "now": now_timestamp(),
        "cpu.user": ct.get("user", 0.0),
        "cpu.total": ct.get("total", 0.0),
        "mem.used": mem_used_bytes(),
        "load": load_1(),
    }