"""
Core monitoring functionality for Glances
"""

import time
import psutil
import platform
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class SystemStats:
    """Container for system statistics"""
    timestamp: float
    cpu_user: float
    cpu_total: float
    mem_used: float
    load: float


class Glances:
    """Main Glances monitoring class"""
    
    def __init__(self):
        self._cpu_times = psutil.cpu_times()
        self._last_cpu_times = self._cpu_times
        self._last_cpu_check = time.time()
    
    def get_stats(self) -> SystemStats:
        """Get current system statistics"""
        current_time = time.time()
        
        # Get CPU usage
        cpu_times = psutil.cpu_times()
        time_diff = current_time - self._last_cpu_check
        
        if time_diff > 0:
            user_diff = cpu_times.user - self._last_cpu_times.user
            total_diff = sum([
                cpu_times.user - self._last_cpu_times.user,
                cpu_times.system - self._last_cpu_times.system,
                cpu_times.idle - self._last_cpu_times.idle,
                cpu_times.nice - self._last_cpu_times.nice if hasattr(cpu_times, 'nice') else 0,
                cpu_times.iowait - self._last_cpu_times.iowait if hasattr(cpu_times, 'iowait') else 0,
                cpu_times.irq - self._last_cpu_times.irq if hasattr(cpu_times, 'irq') else 0,
                cpu_times.softirq - self._last_cpu_times.softirq if hasattr(cpu_times, 'softirq') else 0,
                cpu_times.steal - self._last_cpu_times.steal if hasattr(cpu_times, 'steal') else 0,
                cpu_times.guest - self._last_cpu_times.guest if hasattr(cpu_times, 'guest') else 0,
                cpu_times.guest_nice - self._last_cpu_times.guest_nice if hasattr(cpu_times, 'guest_nice') else 0
            ])
            
            cpu_user_percent = (user_diff / total_diff * 100) if total_diff > 0 else 0
            cpu_total_percent = 100 - ((cpu_times.idle - self._last_cpu_times.idle) / total_diff * 100) if total_diff > 0 else 0
        else:
            cpu_user_percent = 0
            cpu_total_percent = 0
        
        # Update for next call
        self._last_cpu_times = cpu_times
        self._last_cpu_check = current_time
        
        # Get memory usage
        mem = psutil.virtual_memory()
        mem_used_percent = mem.percent
        
        # Get system load (1-minute average)
        if platform.system() == "Windows":
            # Windows doesn't have load average, use CPU utilization as proxy
            load_avg = cpu_total_percent / 100
        else:
            load_avg = psutil.getloadavg()[0]
        
        return SystemStats(
            timestamp=current_time,
            cpu_user=cpu_user_percent,
            cpu_total=cpu_total_percent,
            mem_used=mem_used_percent,
            load=load_avg
        )
    
    def get_csv_row(self, fields: List[str]) -> str:
        """Get CSV row for specified fields"""
        stats = self.get_stats()
        values = []
        
        for field in fields:
            if field == "now":
                values.append(str(stats.timestamp))
            elif field == "cpu.user":
                values.append(f"{stats.cpu_user:.2f}")
            elif field == "cpu.total":
                values.append(f"{stats.cpu_total:.2f}")
            elif field == "mem.used":
                values.append(f"{stats.mem_used:.2f}")
            elif field == "load":
                values.append(f"{stats.load:.2f}")
            else:
                raise ValueError(f"Unknown field: {field}")
        
        return ",".join(values)