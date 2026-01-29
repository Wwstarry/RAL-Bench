"""
Filter utilities for IP parsing and log matching.
"""

import re
import ipaddress
from typing import Optional, List, Tuple, Dict, Any, Pattern


def isValidIP(ip: str) -> bool:
    """
    Check if a string is a valid IP address (IPv4 or IPv6).
    
    Args:
        ip: IP address string
        
    Returns:
        True if valid IP, False otherwise
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def searchIP(text: str) -> Optional[str]:
    """
    Search for an IP address in text.
    
    Args:
        text: Text to search
        
    Returns:
        First IP address found, or None
    """
    # IPv4 pattern
    ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    # IPv6 pattern (simplified)
    ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
    
    # Try IPv4 first
    match = re.search(ipv4_pattern, text)
    if match:
        ip = match.group()
        if isValidIP(ip):
            return ip
    
    # Try IPv6
    match = re.search(ipv6_pattern, text)
    if match:
        ip = match.group()
        if isValidIP(ip):
            return ip
    
    return None


def extractIPs(text: str) -> List[str]:
    """
    Extract all valid IP addresses from text.
    
    Args:
        text: Text to search
        
    Returns:
        List of valid IP addresses found
    """
    ips = []
    
    # IPv4 pattern
    ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    # IPv6 pattern (simplified)
    ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
    
    # Find IPv4 addresses
    for match in re.finditer(ipv4_pattern, text):
        ip = match.group()
        if isValidIP(ip):
            ips.append(ip)
    
    # Find IPv6 addresses
    for match in re.finditer(ipv6_pattern, text):
        ip = match.group()
        if isValidIP(ip):
            ips.append(ip)
    
    return ips


class Filter:
    """Filter for parsing log files and detecting failures."""
    
    def __init__(self, jailname: str, failregex: str, ignoreregex: Optional[str] = None):
        """
        Initialize a filter.
        
        Args:
            jailname: Name of the jail
            failregex: Regex pattern for failure lines
            ignoreregex: Regex pattern for lines to ignore (optional)
        """
        self.jailname = jailname
        self.failregex = re.compile(failregex)
        self.ignoreregex = re.compile(ignoreregex) if ignoreregex else None
        
    def matchLine(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Match a log line against the filter.
        
        Args:
            line: Log line to match
            
        Returns:
            Dictionary with match info if matched, None otherwise
        """
        # Check if line should be ignored
        if self.ignoreregex and self.ignoreregex.search(line):
            return None
        
        # Try to match failure pattern
        match = self.failregex.search(line)
        if match:
            # Extract IP from the matched line
            ip = searchIP(line)
            
            return {
                'line': line,
                'match': match.group(),
                'ip': ip,
                'groups': match.groups(),
                'groupdict': match.groupdict()
            }
        
        return None
    
    def getFailures(self, loglines: List[str]) -> List[Dict[str, Any]]:
        """
        Get all failures from log lines.
        
        Args:
            loglines: List of log lines
            
        Returns:
            List of match dictionaries
        """
        failures = []
        for line in loglines:
            match = self.matchLine(line)
            if match:
                failures.append(match)
        return failures