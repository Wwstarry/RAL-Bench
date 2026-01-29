"""
Module for collecting system statistics using psutil.
"""
import datetime
import sys

try:
    import psutil
except ImportError:
    sys.stderr.write("Error: psutil library not found. Please install it with 'pip install psutil'\n")
    sys.exit(1)

class SystemStats:
    """
    A class to fetch and cache system statistics for a single snapshot.
    This avoids redundant calls to psutil functions within a single run.
    """
    def __init__(self):
        self._cpu_times_percent = None
        self._virtual_mem = None
        self._load_avg = None

    def _get_cpu_times_percent(self):
        """Lazy-loads and caches CPU times."""
        if self._cpu_times_percent is None:
            # A small interval is required for a meaningful first reading.
            self._cpu_times_percent = psutil.cpu_times_percent(interval=0.1, percpu=False)
        return self._cpu_times_percent

    def _get_virtual_mem(self):
        """Lazy-loads and caches virtual memory stats."""
        if self._virtual_mem is None:
            self._virtual_mem = psutil.virtual_memory()
        return self._virtual_mem

    def _get_load_avg(self):
        """Lazy-loads and caches system load average."""
        if self._load_avg is None:
            if hasattr(psutil, 'getloadavg'):
                self._load_avg = psutil.getloadavg()
            else:
                # Provide a default for platforms without load average (e.g., Windows).
                self._load_avg = (0.0, 0.0, 0.0)
        return self._load_avg

    # Public API for individual stats
    def now(self):
        """Returns the current timestamp as a string."""
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def cpu_user(self):
        """Returns the percentage of CPU time spent by user processes."""
        return self._get_cpu_times_percent().user

    def cpu_total(self):
        """
        Returns the total CPU utilization percentage.
        Calculated as 100% minus the idle percentage.
        """
        cpu_times = self._get_cpu_times_percent()
        return 100.0 - cpu_times.idle

    def mem_used(self):
        """Returns the amount of used memory in bytes."""
        return self._get_virtual_mem().used

    def load(self):
        """Returns the 1-minute system load average."""
        return self._get_load_avg()[0]

def get_all_stats_mappers():
    """
    Returns a dictionary mapping stat field names to their getter functions.

    This factory function ensures the SystemStats object is instantiated only
    when stats are actually requested.
    """
    stats_instance = SystemStats()
    return {
        'now': stats_instance.now,
        'cpu.user': stats_instance.cpu_user,
        'cpu.total': stats_instance.cpu_total,
        'mem.used': stats_instance.mem_used,
        'load': stats_instance.load,
    }