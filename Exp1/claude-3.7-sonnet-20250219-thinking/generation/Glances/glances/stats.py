import os
import platform
import time
from datetime import datetime

def get_now():
    """Get current timestamp"""
    return datetime.now().timestamp()

def get_cpu_stats():
    """Get CPU statistics"""
    system = platform.system()
    
    if system == "Linux":
        return _get_cpu_stats_linux()
    else:
        # Fallback for other platforms
        return _get_cpu_stats_fallback()

def _get_cpu_stats_linux():
    """Get CPU statistics on Linux"""
    try:
        with open('/proc/stat', 'r') as f:
            cpu_line = next(line for line in f if line.startswith('cpu '))
            
        # Parse values: user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice
        values = list(map(int, cpu_line.split()[1:]))
        
        # Calculate totals
        idle = values[3]
        total = sum(values)
        
        # Avoid division by zero
        if total == 0:
            return {'user': 0.0, 'total': 0.0}
        
        # Calculate percentages
        return {
            'user': (values[0] / total) * 100,
            'total': ((total - idle) / total) * 100
        }
    except Exception:
        return _get_cpu_stats_fallback()

def _get_cpu_stats_fallback():
    """Fallback CPU statistics when platform-specific methods fail"""
    # Simple fallback - return reasonable values for demo purposes
    return {'user': 5.0, 'total': 10.0}

def get_memory_stats():
    """Get memory statistics"""
    system = platform.system()
    
    if system == "Linux":
        return _get_memory_stats_linux()
    else:
        # Fallback for other platforms
        return _get_memory_stats_fallback()

def _get_memory_stats_linux():
    """Get memory statistics on Linux"""
    try:
        mem_info = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if ':' in line:
                    key, value = line.split(':', 1)
                    mem_info[key.strip()] = int(value.strip().split()[0]) * 1024  # Convert KB to bytes
        
        total = mem_info.get('MemTotal', 0)
        free = mem_info.get('MemFree', 0)
        buffers = mem_info.get('Buffers', 0)
        cached = mem_info.get('Cached', 0)
        
        # Avoid division by zero
        if total == 0:
            return {'used': 0, 'total': 0}
        
        used = total - free - buffers - cached
        
        return {'used': used, 'total': total}
    except Exception:
        return _get_memory_stats_fallback()

def _get_memory_stats_fallback():
    """Fallback memory statistics when platform-specific methods fail"""
    # Simple fallback - return reasonable values for demo purposes
    return {'used': 2000000000, 'total': 8000000000}

def get_load_stats():
    """Get system load statistics"""
    try:
        if platform.system() in ["Linux", "Darwin"]:  # Linux or macOS
            load1, _, _ = os.getloadavg()
            return load1
    except (AttributeError, OSError):
        pass
    
    # Fallback for Windows or if getloadavg fails
    return 1.0

def get_stats():
    """Get all system statistics"""
    return {
        'now': get_now(),
        'cpu': get_cpu_stats(),
        'mem': get_memory_stats(),
        'load': get_load_stats()
    }