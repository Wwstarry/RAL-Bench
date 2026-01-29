import re
import ipaddress

def isValidIP(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def searchIP(text):
    # Regex matches IPv4 and IPv6 addresses
    ip_pattern = r'\b(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[a-fA-F0-9:]+::?[a-fA-F0-9:]*)\b'
    match = re.search(ip_pattern, text)
    return match.group(0) if match else None