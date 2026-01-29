"""
Minimal Jail implementation for Fail2Ban.
Handles filter and action coordination without real banning.
"""
import re
import time
from typing import List, Dict, Any

class Jail:
    """A jail manages filters and actions for monitoring log files."""
    
    def __init__(self, name: str):
        self.name = name
        self.filters = []
        self.actions = []
        self.banned_ips = set()
        self.enabled = True
        self.findtime = 600  # 10 minutes default
        self.bantime = 600   # 10 minutes default
        self.maxretry = 3    # 3 attempts default
        
    def addFilter(self, filter_obj):
        """Add a filter to this jail."""
        self.filters.append(filter_obj)
        
    def addAction(self, action_obj):
        """Add an action to this jail."""
        self.actions.append(action_obj)
        
    def processLine(self, line: str, timestamp: float) -> Dict[str, Any]:
        """
        Process a log line through all filters.
        Returns match information if suspicious activity is detected.
        """
        if not self.enabled:
            return {}
            
        for filter_obj in self.filters:
            match = filter_obj.match(line)
            if match:
                ip_addr = match.get('ip')
                if ip_addr and self._isValidIP(ip_addr):
                    return {
                        'ip': ip_addr,
                        'timestamp': timestamp,
                        'filter': filter_obj.name,
                        'match_data': match
                    }
        return {}
        
    def banIP(self, ip: str) -> bool:
        """Simulate banning an IP address (no real firewall changes)."""
        if self._isValidIP(ip):
            self.banned_ips.add(ip)
            # Simulate action execution
            for action in self.actions:
                action.ban(ip)
            return True
        return False
        
    def unbanIP(self, ip: str) -> bool:
        """Simulate unbanning an IP address."""
        if ip in self.banned_ips:
            self.banned_ips.remove(ip)
            # Simulate action execution
            for action in self.actions:
                action.unban(ip)
            return True
        return False
        
    def _isValidIP(self, ip: str) -> bool:
        """Validate IP address format."""
        from fail2ban.server.filter import isValidIP
        return isValidIP(ip)
        
    def getStatus(self) -> Dict[str, Any]:
        """Return jail status information."""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'banned_ips': list(self.banned_ips),
            'filter_count': len(self.filters),
            'action_count': len(self.actions)
        }