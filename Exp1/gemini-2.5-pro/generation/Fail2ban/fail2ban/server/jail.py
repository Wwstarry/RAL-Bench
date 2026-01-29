import re
from collections import defaultdict
from . import filter as fb_filter

class Jail:
    """
    A Jail object manages the coordination of a filter and actions for a
    particular service. In this minimal implementation, it only handles
    log parsing and failure tracking.
    """
    def __init__(self, name, logpath, failregex):
        """
        Initializes a Jail.

        :param name: The name of the jail (e.g., 'sshd').
        :param logpath: The path to the log file to monitor.
        :param failregex: The regular expression to find failures.
        """
        self.name = name
        self.logpath = logpath
        
        # The failregex should contain a capture group for the IP address.
        # Fail2Ban convention uses <HOST>, which is an alias for a regex pattern.
        # We'll support a named group 'host' or the first capture group.
        try:
            self.failregex = re.compile(failregex)
        except re.error as e:
            raise ValueError(f"Invalid regex for jail '{self.name}': {e}")
        
        self.failures = defaultdict(int)

    def process_log_line(self, line):
        """
        Processes a single log line against the jail's filter. If a failure
        is detected, it records it.

        :param line: The log line string.
        :return: The IP address if a failure was matched, otherwise None.
        """
        match = self.failregex.search(line)
        if match:
            ip = None
            # Try to get IP from named group 'host' first (Fail2Ban convention)
            try:
                ip = match.group('host')
                if not fb_filter.isValidIP(ip):
                    ip = None # Invalidate if it's not a real IP
            except IndexError:
                # Fallback to the first capture group if 'host' is not present
                if match.groups():
                    potential_ip = match.group(1)
                    if fb_filter.isValidIP(potential_ip):
                        ip = potential_ip
            
            if ip:
                self.failures[ip] += 1
                # In a real implementation, we'd check against maxretry,
                # bantime, and then call a banning action.
                return ip
        return None

    def get_failures(self):
        """
        Returns a dictionary of IPs and their failure counts.
        """
        return dict(self.failures)