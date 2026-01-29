"""Jail module for coordinating filters and actions."""

from typing import Dict, List, Optional, Set
from fail2ban.server.filter import Filter


class Jail:
    """
    Jail object that manages a filter and associated actions.
    Coordinates detection of failures and application of actions.
    """
    
    def __init__(self, name: str):
        """
        Initialize a jail.
        
        Args:
            name: Name of the jail.
        """
        self.name = name
        self.filter = Filter(name)
        self.actions = []
        self.bantime = 600  # seconds
        self.findtime = 600  # seconds
        self.maxretry = 5  # max failures before ban
        self.enabled = True
        self.banned_ips: Set[str] = set()
        self.failure_counts: Dict[str, int] = {}
    
    def setFilter(self, filter_obj: Filter) -> None:
        """
        Set the filter for this jail.
        
        Args:
            filter_obj: Filter object to use.
        """
        self.filter = filter_obj
    
    def addAction(self, action_name: str) -> None:
        """
        Add an action to this jail.
        
        Args:
            action_name: Name of the action to add.
        """
        if action_name not in self.actions:
            self.actions.append(action_name)
    
    def setBanTime(self, seconds: int) -> None:
        """
        Set the ban time in seconds.
        
        Args:
            seconds: Ban duration in seconds.
        """
        self.bantime = seconds
    
    def setFindTime(self, seconds: int) -> None:
        """
        Set the find time window in seconds.
        
        Args:
            seconds: Time window in seconds.
        """
        self.findtime = seconds
    
    def setMaxRetry(self, count: int) -> None:
        """
        Set the maximum retry count before banning.
        
        Args:
            count: Maximum number of retries.
        """
        self.maxretry = count
    
    def setEnabled(self, enabled: bool) -> None:
        """
        Enable or disable the jail.
        
        Args:
            enabled: True to enable, False to disable.
        """
        self.enabled = enabled
    
    def processLogLine(self, line: str) -> Optional[str]:
        """
        Process a log line through the filter.
        
        Args:
            line: Log line to process.
            
        Returns:
            IP address if extracted, None otherwise.
        """
        if not self.enabled:
            return None
        
        return self.filter.processLine(line)
    
    def recordFailure(self, ip: str) -> bool:
        """
        Record a failure for an IP address.
        
        Args:
            ip: IP address that failed.
            
        Returns:
            True if IP should be banned, False otherwise.
        """
        if ip not in self.failure_counts:
            self.failure_counts[ip] = 0
        
        self.failure_counts[ip] += 1
        
        if self.failure_counts[ip] >= self.maxretry:
            self.banned_ips.add(ip)
            return True
        
        return False
    
    def getBannedIPs(self) -> List[str]:
        """
        Get list of currently banned IPs.
        
        Returns:
            List of banned IP addresses.
        """
        return sorted(list(self.banned_ips))
    
    def getFailureCount(self, ip: str) -> int:
        """
        Get failure count for an IP.
        
        Args:
            ip: IP address to check.
            
        Returns:
            Number of recorded failures.
        """
        return self.failure_counts.get(ip, 0)
    
    def unban(self, ip: str) -> None:
        """
        Unban an IP address.
        
        Args:
            ip: IP address to unban.
        """
        self.banned_ips.discard(ip)
        if ip in self.failure_counts:
            del self.failure_counts[ip]
    
    def clear(self) -> None:
        """Clear all bans and failure counts."""
        self.banned_ips.clear()
        self.failure_counts.clear()