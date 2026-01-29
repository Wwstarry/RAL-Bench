"""System monitoring functionality."""
import os
import platform
import time

if platform.system() == "Windows":
    import psutil
else:
    import psutil


class SystemMonitor:
    """Cross-platform system monitor."""
    
    def __init__(self):
        self._last_cpu_times = None
        self._last_cpu_time = None
    
    def get_cpu_user(self):
        """Get CPU user percentage."""
        try:
            cpu_times = psutil.cpu_times()
            current_time = time.time()
            
            if self._last_cpu_times is not None and self._last_cpu_time is not None:
                time_delta = current_time - self._last_cpu_time
                user_delta = cpu_times.user - self._last_cpu_times.user
                user_percent = (user_delta / time_delta) * 100
            else:
                user_percent = 0.0
            
            self._last_cpu_times = cpu_times
            self._last_cpu_time = current_time
            
            return max(0.0, min(100.0, user_percent))
        except Exception:
            return 0.0
    
    def get_cpu_total(self):
        """Get total CPU usage percentage."""
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            return 0.0
    
    def get_mem_used(self):
        """Get used memory in bytes."""
        try:
            memory = psutil.virtual_memory()
            return memory.used
        except Exception:
            return 0
    
    def get_load(self):
        """Get system load average."""
        try:
            if hasattr(os, 'getloadavg'):
                return os.getloadavg()[0]  # 1-minute load average
            else:
                # Windows doesn't have load average, approximate with CPU usage
                return self.get_cpu_total() / 100.0
        except Exception:
            return 0.0