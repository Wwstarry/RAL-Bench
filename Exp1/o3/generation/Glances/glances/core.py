"""
Internals – system information helpers.

All functionality lives in the standard library unless `psutil`
is available in the run-time environment; when present we will
take advantage of it for better accuracy.

The module purposefully keeps dependencies to a minimum so that
the generated repository is immediately usable without any extra
installation steps.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Dict

# Optional psutil import (not hard requirement).
try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover  # noqa: BLE001
    psutil = None  # type: ignore


# --------------------------------------------------------------------------- #
# Public helpers                                                              #
# --------------------------------------------------------------------------- #

_SUPPORTED_FIELDS = {
    "now",
    "cpu.user",
    "cpu.total",
    "mem.used",
    "load",
}


def supported_fields() -> set[str]:
    """
    Return the set of field names supported by the `--stdout-csv` interface.
    """
    # We return a copy to protect internal constant.
    return set(_SUPPORTED_FIELDS)


def collect_metrics() -> Dict[str, float]:
    """
    Collect all supported metrics at once and return them in a mapping.

    Notes
    -----
    • Every call performs a *single* sampling to keep the implementation
      predictable and lightweight.
    • Metrics are returned in their “raw” numeric form.  The CLI caller is
      responsible for stringification / formatting.
    """
    metrics: dict[str, float] = {}

    # Timestamp (“now”) – epoch seconds with sub-second resolution discarded
    # to keep the output stable and parseable as an integer.
    metrics["now"] = int(time.time())

    # --------------------------------------------------------------------- #
    # CPU metrics                                                            #
    # --------------------------------------------------------------------- #
    if psutil is not None:
        # psutil is available – use it for accurate readings.
        try:
            # User space CPU percentage.
            cpu_times_percent = psutil.cpu_times_percent(interval=0.1)
            metrics["cpu.user"] = float(getattr(cpu_times_percent, "user", 0.0))

            # Total CPU percentage (all modes combined).
            metrics["cpu.total"] = float(psutil.cpu_percent(interval=0.0))
        except Exception:  # pragma: no cover  # noqa: BLE001
            # Any failure falls back to 0 to keep the command resilient.
            metrics["cpu.user"] = 0.0
            metrics["cpu.total"] = 0.0
    else:
        # psutil not available – we cannot sample percentages portably.
        metrics["cpu.user"] = 0.0
        metrics["cpu.total"] = 0.0

    # --------------------------------------------------------------------- #
    # Memory                                                                 #
    # --------------------------------------------------------------------- #
    if psutil is not None:
        try:
            vm = psutil.virtual_memory()
            metrics["mem.used"] = float(vm.used)
        except Exception:  # pragma: no cover  # noqa: BLE001
            metrics["mem.used"] = 0.0
    else:
        # Fallback for Linux-like operating systems using /proc/meminfo.
        if os.name == "posix" and os.path.isfile("/proc/meminfo"):
            try:
                total_kib = avail_kib = None
                with open("/proc/meminfo", "r", encoding="utf8") as fh:
                    for line in fh:
                        if line.startswith("MemTotal:"):
                            total_kib = int(line.split()[1])
                        elif line.startswith("MemAvailable:"):
                            avail_kib = int(line.split()[1])
                        if total_kib is not None and avail_kib is not None:
                            break
                if total_kib is not None and avail_kib is not None:
                    used_kib = total_kib - avail_kib
                    metrics["mem.used"] = float(used_kib) * 1024.0  # bytes
                else:
                    metrics["mem.used"] = 0.0
            except Exception:  # pragma: no cover  # noqa: BLE001
                metrics["mem.used"] = 0.0
        else:
            # Unknown platform – best effort.
            metrics["mem.used"] = 0.0

    # --------------------------------------------------------------------- #
    # Load average                                                           #
    # --------------------------------------------------------------------- #
    try:
        if hasattr(os, "getloadavg"):
            load1, _, _ = os.getloadavg()
            metrics["load"] = float(load1)
        elif psutil is not None and hasattr(psutil, "getloadavg"):
            # psutil exposes a portable getloadavg on some systems.
            load1, _, _ = psutil.getloadavg()  # type: ignore[attr-defined]
            metrics["load"] = float(load1)
        else:
            # Platform without load average (e.g. Windows).
            metrics["load"] = 0.0
    except Exception:  # pragma: no cover  # noqa: BLE001
        metrics["load"] = 0.0

    # Ensure every supported field is present (robustness).
    for field in _SUPPORTED_FIELDS:
        metrics.setdefault(field, 0.0)

    return metrics