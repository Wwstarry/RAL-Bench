import re
from fail2ban.server.filter import isValidIP, searchIP

class Jail:
    """
    Minimal Jail object: manages filter and actions coordination.
    In this safe subset, only regex matching and IP tracking are performed.
    """
    def __init__(self, name, filter_regex, maxretry=3):
        self.name = name
        self.filter_regex = re.compile(filter_regex)
        self.maxretry = maxretry
        self.failures = {}  # ip -> count

    def process_line(self, line):
        """
        Process a log line. If it matches the filter regex, extract IP and count failure.
        Returns (ip, banned) tuple.
        """
        if self.filter_regex.search(line):
            ip = searchIP(line)
            if ip and isValidIP(ip):
                self.failures[ip] = self.failures.get(ip, 0) + 1
                banned = self.failures[ip] >= self.maxretry
                return ip, banned
        return None, False

    def get_banned(self):
        """Return list of banned IPs."""
        return [ip for ip, count in self.failures.items() if count >= self.maxretry]

    def reset(self):
        """Reset failure counts."""
        self.failures.clear()