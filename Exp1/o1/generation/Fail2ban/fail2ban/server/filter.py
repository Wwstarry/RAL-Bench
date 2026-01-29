import re

def isValidIP(ipAddr):
    """
    Check if the provided string is a valid IPv4 or IPv6 address.
    Returns True if valid, False otherwise.
    """
    # Simple IPv4 check
    pattern_ipv4 = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    # Simple IPv6 check
    pattern_ipv6 = re.compile(r'^([a-fA-F0-9]{0,4}:){2,7}[a-fA-F0-9]{0,4}$')
    if pattern_ipv4.match(ipAddr):
        parts = ipAddr.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    elif pattern_ipv6.match(ipAddr):
        return True
    return False

def searchIP(line):
    """
    Search for an IP (IPv4 or IPv6) in the given log line and
    return the first IP found. Return None if no IP is found.
    """
    # This is a simple pattern to capture IPv4 or IPv6 addresses
    ip_pattern = re.compile(r'(([0-9]{1,3}\.){3}[0-9]{1,3})|([a-fA-F0-9]{0,4}:){2,7}[a-fA-F0-9]{0,4}')
    match = ip_pattern.search(line)
    if match:
        candidate = match.group(0)
        if isValidIP(candidate):
            return candidate
    return None