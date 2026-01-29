import re
import ipaddress

# A regex to find potential IPv4 addresses.
IP_REGEX = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

def isValidIP(ip_str):
    """
    Checks if a string is a valid IP address (IPv4 or IPv6).

    :param ip_str: The string to validate.
    :return: True if valid, False otherwise.
    """
    if not isinstance(ip_str, str):
        return False
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

def searchIP(line):
    """
    Searches for the first valid IP address in a line.
    This is a simplified version. A real implementation would be more robust
    and likely tied to the regex match.

    :param line: The string (log line) to search in.
    :return: The IP address string if found, otherwise None.
    """
    # In a real Fail2Ban, this is more complex and uses <HOST> tag from regex.
    # For this minimal version, we'll just find the first IP-like string and validate it.
    match = IP_REGEX.search(line)
    if match:
        ip = match.group(0)
        if isValidIP(ip):
            return ip
    return None