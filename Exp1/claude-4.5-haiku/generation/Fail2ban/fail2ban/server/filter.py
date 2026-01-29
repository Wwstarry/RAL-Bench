"""Filter module for log parsing and IP extraction."""

import re
import ipaddress
from typing import Optional, List, Tuple


def isValidIP(ip_str: str) -> bool:
    """
    Validate if a string is a valid IPv4 or IPv6 address.
    
    Args:
        ip_str: String to validate as IP address.
        
    Returns:
        True if valid IP address, False otherwise.
    """
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


def searchIP(text: str) -> Optional[str]:
    """
    Search for the first valid IP address in text.
    
    Args:
        text: Text to search for IP address.
        
    Returns:
        First valid IP address found, or None.
    """
    # IPv4 pattern
    ipv4_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    
    match = re.search(ipv4_pattern, text)
    if match:
        ip = match.group(0)
        if isValidIP(ip):
            return ip
    
    return None


def searchIPs(text: str) -> List[str]:
    """
    Search for all valid IP addresses in text.
    
    Args:
        text: Text to search for IP addresses.
        
    Returns:
        List of valid IP addresses found.
    """
    # IPv4 pattern
    ipv4_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    
    matches = re.findall(ipv4_pattern, text)
    return [ip for ip in matches if isValidIP(ip)]


class Filter:
    """
    Filter object for parsing log files and extracting failed login attempts.
    """
    
    def __init__(self, name: str):
        """
        Initialize a filter.
        
        Args:
            name: Name of the filter.
        """
        self.name = name
        self.failregex = None
        self.ignoreregex = None
        self.datepattern = None
    
    def setFailRegex(self, regex: str) -> None:
        """
        Set the regex pattern for matching failures.
        
        Args:
            regex: Regular expression pattern.
        """
        try:
            self.failregex = re.compile(regex)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    
    def setIgnoreRegex(self, regex: str) -> None:
        """
        Set the regex pattern for ignoring lines.
        
        Args:
            regex: Regular expression pattern.
        """
        try:
            self.ignoreregex = re.compile(regex)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    
    def setDatePattern(self, pattern: str) -> None:
        """
        Set the date pattern for log parsing.
        
        Args:
            pattern: Date pattern string.
        """
        self.datepattern = pattern
    
    def processLine(self, line: str) -> Optional[str]:
        """
        Process a log line and extract IP if it matches failure pattern.
        
        Args:
            line: Log line to process.
            
        Returns:
            IP address if line matches failure pattern, None otherwise.
        """
        if self.ignoreregex and self.ignoreregex.search(line):
            return None
        
        if self.failregex and self.failregex.search(line):
            return searchIP(line)
        
        return None