import re

def isValidIP(ip):
    """
    Validate if the given string is a valid IPv4 address.
    """
    pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    if pattern.match(ip):
        parts = ip.split(".")
        return all(0 <= int(part) <= 255 for part in parts)
    return False

def searchIP(line):
    """
    Search for an IP address in a given log line.
    """
    pattern = re.compile(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}")
    match = pattern.search(line)
    return match.group(0) if match else None