import re
import ipaddress

def isValidIP(ip):
    """Check if the given string is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def searchIP(text):
    """Search for the first valid IP address in the given text."""
    # Simple regex to find IPv4 and IPv6 candidates
    # IPv4 regex simplified: 4 groups of 1-3 digits separated by dots
    # IPv6 regex simplified: groups of hex digits separated by colons
    ipv4_pattern = r'(?:\d{1,3}\.){3}\d{1,3}'
    ipv6_pattern = r'([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}'
    for pattern in (ipv4_pattern, ipv6_pattern):
        for match in re.finditer(pattern, text):
            candidate = match.group(0)
            if isValidIP(candidate):
                return candidate
    return None