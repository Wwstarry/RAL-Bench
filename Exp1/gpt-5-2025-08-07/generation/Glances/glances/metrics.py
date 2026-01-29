"""
Metrics collection utilities for the minimal glances-compatible CLI.

This module aims to stay lightweight and avoid heavy dependencies.
If psutil is available, it will be used to acquire system metrics.
Otherwise, platform-specific fallbacks are used when possible.

Supported fields:
- now: current UNIX epoch time (seconds, float)
- cpu.user: percentage of CPU time spent in user mode (float percent)
- cpu.total: overall CPU usage percentage (float percent)
- mem.used: used memory in bytes (int)
- load: 1-minute load average (float)
"""

from __future__ import annotations

import os
import sys
import time
from typing import Optional

try:
    import psutil  # type: ignore
except Exception:
    psutil = None


def get_now() -> float:
    """Return the current UNIX epoch time as a float in seconds."""
    return time.time()


def get_load_avg1() -> float:
    """Return the 1-minute load average; 0.0 if not available."""
    try:
        return float(os.getloadavg()[0])
    except Exception:
        # os.getloadavg not available on some platforms (e.g., Windows)
        return 0.0


def _linux_read_proc_stat_totals() -> Optional[dict]:
    """Read /proc/stat and return a dict with CPU total times, or None if not available."""
    try:
        with open("/proc/stat", "r") as f:
            for line in f:
                if line.startswith("cpu "):
                    parts = line.strip().split()
                    # Expected: cpu user nice system idle iowait irq softirq steal guest guest_nice
                    # We focus on the first 8 (up to steal).
                    # Convert to ints
                    values = [int(x) for x in parts[1:]]
                    # Some minimal validations
                    if len(values) < 4:
                        return None
                    # Build a dictionary for clarity
                    keys = ["user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal"]
                    totals = {}
                    for i, k in enumerate(keys):
                        totals[k] = values[i] if i < len(values) else 0
                    return totals
    except Exception:
        pass
    return None


def _linux_cpu_user_percent_since_boot() -> float:
    """Compute CPU user percent since boot using /proc/stat."""
    totals = _linux_read_proc_stat_totals()
    if not totals:
        return 0.0
    total_time = float(
        totals["user"]
        + totals["nice"]
        + totals["system"]
        + totals["idle"]
        + totals["iowait"]
        + totals["irq"]
        + totals["softirq"]
        + totals["steal"]
    )
    if total_time <= 0.0:
        return 0.0
    user_time = float(totals["user"] + totals["nice"])
    return (user_time / total_time) * 100.0


def _linux_cpu_total_percent_since_boot() -> float:
    """Compute overall CPU usage percent since boot using /proc/stat."""
    totals = _linux_read_proc_stat_totals()
    if not totals:
        return 0.0
    total_time = float(
        totals["user"]
        + totals["nice"]
        + totals["system"]
        + totals["idle"]
        + totals["iowait"]
        + totals["irq"]
        + totals["softirq"]
        + totals["steal"]
    )
    if total_time <= 0.0:
        return 0.0
    # Consider idle + iowait as idle-ish; remaining is 'used'
    idle_like = float(totals["idle"] + totals["iowait"])
    used = total_time - idle_like
    return (used / total_time) * 100.0


def _linux_mem_used_bytes() -> int:
    """Compute used memory in bytes using /proc/meminfo."""
    meminfo = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if ":" in line:
                    key, val = line.split(":", 1)
                    meminfo[key.strip()] = val.strip()
    except Exception:
        return 0

    def parse_kb(key: str) -> Optional[int]:
        val = meminfo.get(key)
        if val is None:
            return None
        # Typical format: "123456 kB"
        parts = val.split()
        try:
            kb = int(parts[0])
            return kb
        except Exception:
            return None

    total_kb = parse_kb("MemTotal")
    avail_kb = parse_kb("MemAvailable")
    if total_kb is not None and avail_kb is not None:
        used_kb = total_kb - avail_kb
        return int(used_kb * 1024)
    # Fallback if MemAvailable is missing: use MemFree + Buffers + Cached
    free_kb = parse_kb("MemFree") or 0
    buffers_kb = parse_kb("Buffers") or 0
    cached_kb = parse_kb("Cached") or 0
    if total_kb is not None:
        used_kb = total_kb - (free_kb + buffers_kb + cached_kb)
        return int(used_kb * 1024)
    return 0


def _win_mem_used_bytes() -> int:
    """Compute used memory in bytes on Windows using ctypes."""
    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total = int(stat.ullTotalPhys)
        avail = int(stat.ullAvailPhys)
        used = total - avail
        if used < 0:
            used = 0
        return used
    except Exception:
        return 0


def get_mem_used_bytes() -> int:
    """Return used memory in bytes."""
    # Prefer psutil if available
    if psutil is not None:
        try:
            vm = psutil.virtual_memory()
            return int(vm.used)
        except Exception:
            pass
    # Fallback by platform
    if sys.platform.startswith("linux"):
        return _linux_mem_used_bytes()
    if sys.platform.startswith("win"):
        return _win_mem_used_bytes()
    # macOS and other Unix-like: try psutil; otherwise try 'vm_stat' via subprocess
    try:
        import subprocess

        out = subprocess.check_output(["vm_stat"], text=True)
        page_size = 4096  # default; will try to parse if available
        for line in out.splitlines():
            if "page size of" in line and "bytes" in line:
                # e.g., "Mach Virtual Memory Statistics: (page size of 4096 bytes)"
                try:
                    page_size = int(line.split("page size of")[1].split("bytes")[0].strip())
                except Exception:
                    pass
        stats = {}
        for line in out.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                # e.g., "Pages free: 12345."
                val_num = "".join(ch for ch in val if ch.isdigit())
                if val_num:
                    try:
                        stats[key.strip()] = int(val_num)
                    except Exception:
                        pass
        # Approximate used = total - free; macOS vm_stat doesn't give total easily
        # Use active + wired + compressed as used approximation if present.
        used_pages = 0
        for k in ("Pages active", "Pages wired down", "Pages occupied by compressor", "Pages speculative"):
            used_pages += int(stats.get(k, 0))
        used_bytes = used_pages * page_size
        return int(used_bytes)
    except Exception:
        return 0


def get_cpu_user_percent() -> float:
    """Return CPU user percentage."""
    if psutil is not None:
        try:
            # Non-blocking snapshot. First call may return 0.0; acceptable here.
            pct = float(psutil.cpu_times_percent(interval=0.0).user)
            return pct
        except Exception:
            pass
    if sys.platform.startswith("linux"):
        return _linux_cpu_user_percent_since_boot()
    # Other platforms without psutil: fallback to 0.0
    return 0.0


def get_cpu_total_percent() -> float:
    """Return overall CPU usage percentage."""
    if psutil is not None:
        try:
            pct = float(psutil.cpu_percent(interval=0.0))
            return pct
        except Exception:
            pass
    if sys.platform.startswith("linux"):
        return _linux_cpu_total_percent_since_boot()
    return 0.0