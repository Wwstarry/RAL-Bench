import time
import platform

try:
    import psutil
except ImportError:
    psutil = None


def get_metrics():
    """
    Returns a dict with keys:
      - now: ISO8601 timestamp string
      - cpu.user: float percentage of user CPU usage (0-100)
      - cpu.total: float percentage of total CPU usage (0-100)
      - mem.used: int bytes used memory
      - load: float 1-minute load average (or 0.0 on Windows)
    """
    now = time.strftime("%Y-%m-%dT%H:%M:%S")

    if psutil is None:
        # Fallback: minimal dummy values
        cpu_user = 0.0
        cpu_total = 0.0
        mem_used = 0
        load = 0.0
    else:
        # cpu_percent with interval=0.1 to get recent usage
        cpu_times_percent = psutil.cpu_times_percent(interval=0.1, percpu=False)
        cpu_user = cpu_times_percent.user
        cpu_total = psutil.cpu_percent(interval=0.1)

        vm = psutil.virtual_memory()
        mem_used = vm.used

        if platform.system() != "Windows":
            try:
                load = psutil.getloadavg()[0]
            except (AttributeError, OSError):
                load = 0.0
        else:
            load = 0.0

    return {
        "now": now,
        "cpu.user": cpu_user,
        "cpu.total": cpu_total,
        "mem.used": mem_used,
        "load": load,
    }