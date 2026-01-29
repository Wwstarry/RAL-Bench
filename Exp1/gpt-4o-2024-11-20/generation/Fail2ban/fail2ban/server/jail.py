import re
from fail2ban.server.filter import isValidIP, searchIP

class Jail:
    """
    Represents a Fail2Ban jail, which monitors log files for suspicious activity
    and coordinates actions based on filters and rules.
    """

    def __init__(self, name, logpath, maxretry, findtime):
        self.name = name
        self.logpath = logpath
        self.maxretry = maxretry
        self.findtime = findtime
        self.failed_attempts = {}

    def process_log_line(self, line):
        """
        Process a single line from the log file. If an IP is found and matches
        suspicious activity, it is added to the failed attempts dictionary.
        """
        ip = searchIP(line)
        if ip and isValidIP(ip):
            self.failed_attempts[ip] = self.failed_attempts.get(ip, 0) + 1
            if self.failed_attempts[ip] > self.maxretry:
                self._trigger_action(ip)

    def _trigger_action(self, ip):
        """
        Placeholder for triggering an action (e.g., banning an IP).
        This implementation only logs the action for testing purposes.
        """
        print(f"Action triggered for IP: {ip}")

    def reset(self):
        """
        Reset the jail's state (e.g., clear failed attempts).
        """
        self.failed_attempts.clear()