from __future__ import annotations

import os
import time
from typing import Optional, Tuple


def _read_first_line(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.readline()
    except OSError:
        return None


def _linux_cpu_times() -> Optional[Tuple[int, int, int, int, int, int, int, int, int, int]]:
    line = _read_first_line("/proc/stat")
    if not line or not line.startswith("cpu "):
        return None
    parts = line.split()
    if len(parts) < 11:
        return None
    try:
        vals = tuple(int(x) for x in parts[1:11])
        return vals  # user,nice,system,idle,iowait,irq,softirq,steal,guest,guest_nice
    except ValueError:
        return None


def _linux_meminfo() -> Optional[dict]:
    try:
        with open("/proc/meminfo", "r", encoding="utf-8", errors="replace") as f:
            d = {}
            for line in f:
                if ":" not in line:
                    continue
                k, rest = line.split(":", 1)
                v = rest.strip().split()
                if not v:
                    continue
                try:
                    d[k] = int(v[0])
                except ValueError:
                    continue
            return d
    except OSError:
        return None


def cpu_total_percent() -> float:
    """
    Return an approximate CPU total utilization percent (0..100+).

    Fast path on Linux uses /proc/stat with a very short sampling interval.
    Fallback returns 0.0 if not available.
    """
    t1 = _linux_cpu_times()
    if t1 is None:
        return 0.0
    time.sleep(0.02)
    t2 = _linux_cpu_times()
    if t2 is None:
        return 0.0

    idle1 = t1[3] + t1[4]
    idle2 = t2[3] + t2[4]
    total1 = sum(t1[:8])
    total2 = sum(t2[:8])

    dt_total = total2 - total1
    dt_idle = idle2 - idle1
    if dt_total <= 0:
        return 0.0
    usage = (dt_total - dt_idle) / dt_total * 100.0
    if usage < 0:
        usage = 0.0
    return usage


def cpu_user_percent() -> float:
    """
    Return an approximate CPU user utilization percent.
    Linux-only; fallback 0.0.
    """
    t1 = _linux_cpu_times()
    if t1 is None:
        return 0.0
    time.sleep(0.02)
    t2 = _linux_cpu_times()
    if t2 is None:
        return 0.0

    user1 = t1[0] + t1[1]
    user2 = t2[0] + t2[1]
    total1 = sum(t1[:8])
    total2 = sum(t2[:8])

    dt_total = total2 - total1
    dt_user = user2 - user1
    if dt_total <= 0:
        return 0.0
    usage = dt_user / dt_total * 100.0
    if usage < 0:
        usage = 0.0
    return usage


def mem_used_bytes() -> int:
    """
    Return used memory in bytes.

    Linux path uses /proc/meminfo and approximates used as:
      MemTotal - MemAvailable (preferred) else MemTotal - MemFree - Buffers - Cached.

    Fallback:
      - On Windows/macOS without external deps, return 0.
    """
    mi = _linux_meminfo()
    if mi is None:
        return 0

    total_kb = mi.get("MemTotal")
    if not total_kb:
        return 0

    if "MemAvailable" in mi:
        used_kb = total_kb - mi.get("MemAvailable", 0)
        return int(used_kb) * 1024

    used_kb = total_kb
    used_kb -= mi.get("MemFree", 0)
    used_kb -= mi.get("Buffers", 0)
    used_kb -= mi.get("Cached", 0)
    if used_kb < 0:
        used_kb = 0
    return int(used_kb) * 1024


def load_one() -> float:
    """
    Return 1-minute load average.

    Cross-platform: uses os.getloadavg where available; otherwise 0.0.
    """
    if hasattr(os, "getloadavg"):
        try:
            return float(os.getloadavg()[0])
        except OSError:
            return 0.0
    return 0.0