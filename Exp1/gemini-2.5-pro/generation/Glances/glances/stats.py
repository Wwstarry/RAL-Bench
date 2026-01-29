# glances/stats.py

import datetime
import sys
import psutil

class GlancesStats:
    """A class to fetch system statistics in a cross-platform way."""

    def __init__(self):
        """Initialize and pre-fetch stats that require an interval."""
        # A small interval is necessary for cpu_times_percent to return
        # meaningful non-zero values on the first call.
        self._cpu = psutil.cpu_times_percent(interval=0.1, percpu=False)
        self._mem = psutil.virtual_memory()
        try:
            # getloadavg() returns a tuple of (1min, 5min, 15min) load averages.
            # It is not available on Windows.
            self._load = psutil.getloadavg()
        except AttributeError:
            # Fallback for Windows.
            self._load = (0.0, 0.0, 0.0)

    def get_value(self, field):
        """
        Get a single stat value by its field name.
        Raises KeyError for unknown fields.
        """
        if field == 'now':
            return datetime.datetime.now().isoformat()
        elif field == 'cpu.user':
            return self._cpu.user
        elif field == 'cpu.total':
            # Total CPU is everything that is not idle.
            return 100.0 - self._cpu.idle
        elif field == 'mem.used':
            return self._mem.used
        elif field == 'load':
            # Return the 1-minute load average.
            return self._load[0]
        else:
            raise KeyError(f"Unknown field: '{field}'")