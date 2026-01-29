"""Core monitoring functionality for Glances."""

import psutil
import time
from datetime import datetime


class GlancesCore:
    """Main class for system monitoring."""

    def __init__(self):
        """Initialize the Glances core."""
        self.stats = {}
        self.update()

    def update(self):
        """Update all system statistics."""
        self.stats = {
            "now": datetime.now().isoformat(),
            "cpu": self._get_cpu_stats(),
            "mem": self._get_mem_stats(),
            "load": self._get_load_stats(),
        }

    def _get_cpu_stats(self):
        """Get CPU statistics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_times = psutil.cpu_times()
        total_time = sum(cpu_times)
        
        return {
            "user": cpu_times.user,
            "total": total_time,
            "percent": cpu_percent,
        }

    def _get_mem_stats(self):
        """Get memory statistics."""
        mem = psutil.virtual_memory()
        return {
            "used": mem.used,
            "total": mem.total,
            "percent": mem.percent,
        }

    def _get_load_stats(self):
        """Get load average."""
        load_avg = psutil.getloadavg()
        return load_avg[0]

    def get_field(self, field_name):
        """Get a specific field value by dot-notation path."""
        parts = field_name.split(".")
        value = self.stats
        
        for part in parts:
            if isinstance(value, dict):
                if part not in value:
                    return None
                value = value[part]
            else:
                return None
        
        return value

    def get_csv_line(self, fields):
        """Generate a CSV line for the specified fields."""
        values = []
        for field in fields:
            value = self.get_field(field)
            if value is None:
                raise ValueError(f"Unknown field: {field}")
            values.append(str(value))
        return ",".join(values)