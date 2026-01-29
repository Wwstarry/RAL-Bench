"""
Filter utilities for IP parsing and validation
"""

import re
import socket


def isValidIP(ip_str):
    """
    Check if a string is a valid IPv4 or IPv6 address.
    
    Args:
        ip_str: String to validate
        
    Returns:
        True if valid IP, False otherwise
    """
    if not ip_str:
        return False
    
    # Try IPv4
    try:
        socket.inet_pton(socket.AF_INET, ip_str)
        return True
    except (socket.error, OSError):
        pass
    
    # Try IPv6
    try:
        socket.inet_pton(socket.AF_INET6, ip_str)
        return True
    except (socket.error, OSError):
        pass
    
    return False


def searchIP(text):
    """
    Search for IP addresses in text.
    
    Args:
        text: Text to search
        
    Returns:
        List of IP addresses found
    """
    if not text:
        return []
    
    ips = []
    
    # IPv4 pattern
    ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    
    # Find all potential IPv4 addresses
    for match in re.finditer(ipv4_pattern, text):
        ip = match.group(0)
        if isValidIP(ip):
            ips.append(ip)
    
    # IPv6 pattern (simplified)
    ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
    
    for match in re.finditer(ipv6_pattern, text):
        ip = match.group(0)
        if isValidIP(ip):
            ips.append(ip)
    
    return ips


class Filter:
    """
    Base filter class for log file monitoring
    """
    
    def __init__(self, jail_name):
        self.jail_name = jail_name
        self.failregex = []
        self.ignoreregex = []
        self.max_retry = 5
        self.find_time = 600
        self.failures = {}
    
    def addFailRegex(self, regex):
        """Add a failure regex pattern"""
        self.failregex.append(re.compile(regex))
    
    def addIgnoreRegex(self, regex):
        """Add an ignore regex pattern"""
        self.ignoreregex.append(re.compile(regex))
    
    def processLine(self, line):
        """
        Process a log line and extract IPs if it matches fail patterns.
        
        Args:
            line: Log line to process
            
        Returns:
            List of IPs that should be banned
        """
        # Check ignore patterns first
        for pattern in self.ignoreregex:
            if pattern.search(line):
                return []
        
        # Check fail patterns
        ips_to_ban = []
        for pattern in self.failregex:
            match = pattern.search(line)
            if match:
                # Extract IPs from the line
                ips = searchIP(line)
                for ip in ips:
                    if ip not in self.failures:
                        self.failures[ip] = 0
                    self.failures[ip] += 1
                    
                    if self.failures[ip] >= self.max_retry:
                        ips_to_ban.append(ip)
        
        return ips_to_ban