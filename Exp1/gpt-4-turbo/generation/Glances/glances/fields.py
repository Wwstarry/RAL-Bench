import time
import sys

try:
    import psutil
except ImportError:
    psutil = None

def get_now():
    # Return current unix timestamp as float
    return time.time()

def get_cpu_user():
    if not psutil:
        raise RuntimeError("psutil is required for cpu.user")
    # Return user cpu percent
    # psutil.cpu_times_percent returns a namedtuple with .user
    # We use interval=0.0 for non-blocking, instantaneous value
    try:
        cpu_times = psutil.cpu_times_percent(interval=0.0)
        return float(cpu_times.user)
    except Exception:
        # Fallback: try cpu_percent
        return float(psutil.cpu_percent(interval=0.0))

def get_cpu_total():
    if not psutil:
        raise RuntimeError("psutil is required for cpu.total")
    # Return total cpu percent
    return float(psutil.cpu_percent(interval=0.0))

def get_mem_used():
    if not psutil:
        raise RuntimeError("psutil is required for mem.used")
    # Return used memory in bytes
    mem = psutil.virtual_memory()
    return float(mem.used)

def get_load():
    # Return 1-minute load average
    # On Windows, os.getloadavg() is not available
    try:
        import os
        load1 = os.getloadavg()[0]
        return float(load1)
    except (AttributeError, OSError):
        # On Windows, approximate with cpu percent / 100 * cpu count
        if not psutil:
            raise RuntimeError("psutil is required for load on this platform")
        cpu_percent = psutil.cpu_percent(interval=0.0)
        cpu_count = psutil.cpu_count() or 1
        # Approximate: load = cpu_percent / 100 * cpu_count
        return float(cpu_percent) / 100.0 * cpu_count

FIELD_MAP = {
    "now": get_now,
    "cpu.user": get_cpu_user,
    "cpu.total": get_cpu_total,
    "mem.used": get_mem_used,
    "load": get_load,
}

def get_field_value(field):
    if field not in FIELD_MAP:
        raise KeyError(field)
    return FIELD_MAP[field]()