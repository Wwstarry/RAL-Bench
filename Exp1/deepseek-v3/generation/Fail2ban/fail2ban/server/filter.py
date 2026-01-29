"""
IP parsing and validation utilities for Fail2Ban.
"""
import re
import ipaddress
from typing import Optional, List, Dict, Any

def isValidIP(ip: str) -> bool:
    """
    Validate if a string is a valid IP address (IPv4 or IPv6).
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def searchIP(text: str) -> Optional[str]:
    """
    Search for IP addresses in text and return the first match.
    """
    # IPv4 pattern
    ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    # IPv6 pattern (simplified)
    ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F]{1,4}\b'
    
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

class Filter:
    """A filter defines patterns to match in log files."""
    
    def __init__(self, name: str, pattern: str):
        self.name = name
        self.pattern = pattern
        self.regex = re.compile(pattern)
        
    def match(self, line: str) -> Dict[str, Any]:
        """
        Match a line against the filter pattern.
        Returns match data including IP address if found.
        """
        match = self.regex.search(line)
        if match:
            result = {
                'matched': match.group(),
                'groups': match.groups(),
                'groupdict': match.groupdict()
            }
            # Extract IP from the matched text
            ip = searchIP(line)
            if ip:
                result['ip'] = ip
            return result
        return {}
        
    def test(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Test multiple lines and return all matches.
        """
        matches = []
        for line in lines:
            match = self.match(line)
            if match:
                matches.append({
                    'line': line,
                    'match': match
                })
        return matches