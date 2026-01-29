import os
import time

try:
    import psutil
except ImportError:
    psutil = None

def get_now():
    # Return current time (epoch seconds)
    return int(time.time())

def get_cpu_user():
    # CPU user percentage
    if not psutil:
        return 0.0
    return psutil.cpu_times_percent(interval=None).user

def get_cpu_total():
    # Total CPU usage percentage
    if not psutil:
        return 0.0
    return psutil.cpu_percent(interval=None)

def get_mem_used():
    # Used memory in bytes
    if not psutil:
        return 0
    return psutil.virtual_memory().used

def get_load():
    # 1-minute load average (if supported), else 0
    if hasattr(os, "getloadavg"):
        return os.getloadavg()[0]
    return 0.0

FIELD_FUNCTIONS = {
    "now": get_now,
    "cpu.user": get_cpu_user,
    "cpu.total": get_cpu_total,
    "mem.used": get_mem_used,
    "load": get_load,
}