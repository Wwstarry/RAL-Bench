import time
import psutil
import os

def get_system_metrics():
    """
    Collect system metrics for CPU, memory, and load.
    Returns a dictionary with the following keys:
    - now: Current timestamp
    - cpu.user: Percentage of CPU usage by user processes
    - cpu.total: Total CPU usage percentage
    - mem.used: Used memory in bytes
    - load: System load average over the last minute
    """
    now = time.time()
    cpu_times = psutil.cpu_times_percent(interval=None)
    cpu_user = cpu_times.user
    cpu_total = sum([cpu_times.user, cpu_times.system, cpu_times.idle])
    mem = psutil.virtual_memory()
    mem_used = mem.used
    load = os.getloadavg()[0]  # 1-minute load average

    return {
        "now": now,
        "cpu.user": cpu_user,
        "cpu.total": cpu_total,
        "mem.used": mem_used,
        "load": load,
    }