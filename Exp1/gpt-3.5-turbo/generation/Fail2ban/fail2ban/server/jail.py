import re
from fail2ban.server import filter as filter_mod

class Jail:
    def __init__(self, name, filter_regex, maxretry=3, findtime=600, bantime=600):
        """
        Initialize a Jail instance.

        :param name: Name of the jail.
        :param filter_regex: Regex pattern string to match log lines.
        :param maxretry: Number of failures before banning.
        :param findtime: Time window (seconds) to count failures.
        :param bantime: Ban duration (seconds) - no real banning here.
        """
        self.name = name
        self.filter_regex = re.compile(filter_regex)
        self.maxretry = maxretry
        self.findtime = findtime
        self.bantime = bantime

        # Internal state: dict of IP -> list of failure timestamps (ints)
        self.failures = {}

        # Banned IPs with ban start timestamp (int)
        self.banned = {}

    def process_line(self, line, timestamp):
        """
        Process a single log line with associated timestamp.

        :param line: Log line string.
        :param timestamp: Integer timestamp (e.g. epoch seconds).
        :return: True if IP is banned due to this line, else False.
        """
        if not self.filter_regex.search(line):
            return False

        ip = filter_mod.searchIP(line)
        if ip is None:
            return False

        # Clean old failures outside findtime window
        self._cleanup_failures(ip, timestamp)

        # Add this failure
        self.failures.setdefault(ip, []).append(timestamp)

        # Check if IP is already banned and if ban expired
        if ip in self.banned:
            if timestamp - self.banned[ip] > self.bantime:
                del self.banned[ip]
            else:
                return True  # still banned

        # Check if failures exceed maxretry
        if len(self.failures[ip]) >= self.maxretry:
            self.banned[ip] = timestamp
            return True

        return False

    def _cleanup_failures(self, ip, current_time):
        """Remove failure timestamps outside the findtime window."""
        if ip not in self.failures:
            return
        window_start = current_time - self.findtime
        self.failures[ip] = [t for t in self.failures[ip] if t >= window_start]
        if not self.failures[ip]:
            del self.failures[ip]

    def is_banned(self, ip, current_time):
        """Check if an IP is currently banned."""
        if ip not in self.banned:
            return False
        if current_time - self.banned[ip] > self.bantime:
            del self.banned[ip]
            return False
        return True