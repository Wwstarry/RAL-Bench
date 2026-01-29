# fail2ban/server/filter.py
import re
import ipaddress

# A simple regex to find an IP address.
# Fail2Ban's real regex is more complex, but this is a minimal subset.
IP_REGEX = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'

def isValidIP(ip):
    """
    Checks if a given string is a valid IP address (IPv4 or IPv6).
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def searchIP(line):
    """
    Searches for the first valid IP address in a line.
    """
    match = re.search(IP_REGEX, line)
    if match:
        ip = match.group(0)
        if isValidIP(ip):
            return ip
    return None

class Filter:
    """
    A filter object that uses regex to find failures in log lines.
    """
    def __init__(self, failregex):
        if isinstance(failregex, str):
            failregex = [failregex]
        # In a real implementation, <HOST> would be replaced with a more
        # specific regex. For this subset, we assume the provided regex
        # is sufficient to cause a match on the line, and we'll find the
        # IP separately.
        self._failregex = [re.compile(r.replace('<HOST>', IP_REGEX)) for r in failregex]

    def getFailures(self, line):
        """
        Check a line against all failregex patterns.
        Returns the IP address if a match is found, otherwise None.
        """
        for regex in self._failregex:
            match = regex.search(line)
            if match:
                # In a real implementation, we'd extract the IP from a group.
                # For this minimal version, we'll just search the whole line.
                ip = searchIP(line)
                if ip:
                    return ip
        return None