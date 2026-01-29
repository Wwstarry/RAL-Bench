import re
import ipaddress

def isValidIP(ip):
    """Check if the given string is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def searchIP(line):
    """Search for the first valid IP address in the given log line."""
    # Simple regex for IPv4 and IPv6 addresses
    ipv4_re = r'(?:(?:\d{1,3}\.){3}\d{1,3})'
    ipv6_re = r'([a-fA-F0-9:]+:+)+[a-fA-F0-9]+'
    for regex in [ipv4_re, ipv6_re]:
        match = re.search(regex, line)
        if match:
            ip = match.group(0)
            if isValidIP(ip):
                return ip
    return None

def findAllIPs(line):
    """Find all valid IP addresses in the given log line."""
    ipv4_re = r'(?:(?:\d{1,3}\.){3}\d{1,3})'
    ipv6_re = r'([a-fA-F0-9:]+:+)+[a-fA-F0-9]+'
    ips = []
    for regex in [ipv4_re, ipv6_re]:
        for match in re.findall(regex, line):
            if isValidIP(match):
                ips.append(match)
    return ips