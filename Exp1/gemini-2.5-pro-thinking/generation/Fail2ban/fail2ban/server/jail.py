# fail2ban/server/jail.py
from collections import defaultdict
import time
from .filter import Filter

class Jail:
    """
    Manages a "jail" for a specific service.
    It uses a filter to detect failures and tracks them.
    If an IP exceeds maxretry, it is "banned".
    """
    def __init__(self, name, logpath, failregex, maxretry=5, findtime=600):
        self.name = name
        self.logpath = logpath
        self.filter = Filter(failregex)
        self.maxretry = int(maxretry)
        self.findtime = int(findtime)
        self.failures = defaultdict(list)
        self.banned = set()

    def process_line(self, line):
        """
        Processes a single log line.
        """
        ip = self.filter.getFailures(line)
        if ip:
            self._add_failure(ip)
            if self._check_ban(ip):
                self.ban_ip(ip)

    def _add_failure(self, ip):
        """
        Adds a failure timestamp for a given IP.
        """
        current_time = time.time()
        # Remove old failures
        self.failures[ip] = [t for t in self.failures[ip] if current_time - t < self.findtime]
        # Add new failure
        self.failures[ip].append(current_time)
        # print(f"[{self.name}] Found failure for {ip}. Count: {len(self.failures[ip])}/{self.maxretry}")

    def _check_ban(self, ip):
        """
        Checks if an IP has reached the maxretry limit within findtime.
        """
        return len(self.failures[ip]) >= self.maxretry

    def ban_ip(self, ip):
        """
        "Bans" an IP. In this simulation, it just adds it to a set.
        """
        if ip not in self.banned:
            # print(f"[{self.name}] Banning {ip}")
            self.banned.add(ip)

    def is_banned(self, ip):
        return ip in self.banned