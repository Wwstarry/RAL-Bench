import re

class Filter(object):
    """
    Base Filter class for handling log parsing.
    """
    def __init__(self, jail):
        self.jail = jail
        self.failRegex = []
        self.ignoreRegex = []

    def addFailRegex(self, regex):
        self.failRegex.append(regex)

def isValidIP(ip):
    """
    Checks if the string is a valid IP address.
    Minimal implementation for IPv4.
    """
    # Simple IPv4 regex
    ipv4_pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return re.match(ipv4_pattern, ip) is not None

def searchIP(text):
    """
    Searches for an IP address in the text.
    Returns a match object or None.
    """
    # Simple IPv4 extraction regex
    ipv4_extract = r'((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
    return re.search(ipv4_extract, text)