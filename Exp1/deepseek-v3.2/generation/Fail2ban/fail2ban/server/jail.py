"""
Jail class - manages filter and action coordination.
This is a minimal implementation for safe offline testing.
"""

import re
import time
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta


class Jail:
    """Jail object that coordinates filters and actions."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize a jail.
        
        Args:
            name: Jail name
            config: Configuration dictionary
        """
        self.name = name
        self.config = config
        self.filter = None
        self.actions = []
        self.banned_ips: Set[str] = set()
        self.failures: Dict[str, List[datetime]] = {}
        
        # Parse configuration
        self.findtime = int(config.get('findtime', 600))  # seconds
        self.bantime = int(config.get('bantime', 600))  # seconds
        self.maxretry = int(config.get('maxretry', 5))
        self.enabled = config.get('enabled', 'true').lower() == 'true'
        
    def setFilter(self, filter_obj: Any) -> None:
        """Set the filter for this jail."""
        self.filter = filter_obj
        
    def addAction(self, action: Any) -> None:
        """Add an action to this jail."""
        self.actions.append(action)
        
    def putFailTicket(self, ip: str, timestamp: Optional[datetime] = None) -> None:
        """
        Record a failure for an IP address.
        
        Args:
            ip: IP address
            timestamp: Failure timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        if ip not in self.failures:
            self.failures[ip] = []
            
        self.failures[ip].append(timestamp)
        
        # Clean old failures
        self._cleanOldFailures(ip)
        
        # Check if we should ban
        if self._shouldBan(ip):
            self.banIP(ip)
            
    def _cleanOldFailures(self, ip: str) -> None:
        """Remove failures older than findtime."""
        if ip not in self.failures:
            return
            
        cutoff = datetime.now() - timedelta(seconds=self.findtime)
        self.failures[ip] = [
            ts for ts in self.failures[ip] 
            if ts > cutoff
        ]
        
        # Remove empty lists
        if not self.failures[ip]:
            del self.failures[ip]
            
    def _shouldBan(self, ip: str) -> bool:
        """Check if an IP should be banned based on failures."""
        if ip not in self.failures:
            return False
            
        recent_failures = self.failures[ip]
        
        # Check if we have enough failures within findtime
        if len(recent_failures) >= self.maxretry:
            return True
            
        return False
        
    def banIP(self, ip: str) -> None:
        """
        Ban an IP address.
        
        Note: In this safe implementation, we only track banned IPs
        without actually modifying firewall rules.
        """
        if ip not in self.banned_ips:
            self.banned_ips.add(ip)
            print(f"[SAFE MODE] Would ban IP: {ip} for {self.bantime} seconds")
            
            # Schedule unban (simulated)
            self._scheduleUnban(ip)
            
    def _scheduleUnban(self, ip: str) -> None:
        """Schedule IP to be unbanned after bantime (simulated)."""
        # In a real implementation, this would use a timer
        # For safe testing, we just track it
        pass
        
    def unbanIP(self, ip: str) -> None:
        """Unban an IP address."""
        if ip in self.banned_ips:
            self.banned_ips.remove(ip)
            print(f"[SAFE MODE] Would unban IP: {ip}")
            
    def getFailTotal(self) -> int:
        """Get total number of failure records."""
        total = 0
        for failures in self.failures.values():
            total += len(failures)
        return total
        
    def getBannedIPs(self) -> List[str]:
        """Get list of currently banned IPs."""
        return list(self.banned_ips)
        
    def isBanned(self, ip: str) -> bool:
        """Check if an IP is currently banned."""
        return ip in self.banned_ips