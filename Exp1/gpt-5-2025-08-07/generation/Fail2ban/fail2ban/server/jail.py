"""
Minimal Jail implementation for a safe subset of Fail2Ban.

Jail coordinates a Filter and in-memory ban logic (no firewall changes).
It processes log lines, tracks failures per IP within a time window, and
marks IPs as banned if maxretry threshold is reached.

This is designed for offline testing/validation and does not run a daemon,
does not require root, and does not interact with system firewalls.
"""
import time
from typing import Optional, Dict, List, Tuple, Any, Set

from .filter import Filter, searchIP


class Jail:
    """
    Jail(name, filter, maxretry, findtime, bantime)

    - name: identifier for the jail
    - filter: Filter instance; if None, a no-op filter is used (matches nothing)
    - maxretry: number of failures within findtime to trigger a ban
    - findtime: time window (seconds) to count failures
    - bantime: ban duration (seconds)

    Methods:
      - process_line(line, timestamp=None) -> dict
      - get_fail_count(ip, now=None) -> int
      - should_ban(ip, now=None) -> bool
      - ban(ip, now=None) -> None
      - is_banned(ip, now=None) -> bool
      - unban_expired(now=None) -> None
      - get_status(now=None) -> dict
    """

    def __init__(
        self,
        name: str,
        filter: Optional[Filter] = None,
        maxretry: int = 5,
        findtime: int = 600,
        bantime: int = 600,
    ):
        self.name = name
        self.filter = filter or Filter(name=f"{name}-noop", failregex=[], ignoreregex=[])
        self.maxretry = int(maxretry)
        self.findtime = int(findtime)
        self.bantime = int(bantime)

        # per-ip list of failure timestamps
        self._failures: Dict[str, List[float]] = {}
        # banned IPs with expiry timestamps
        self._banned: Dict[str, float] = {}

    def _now(self) -> float:
        return time.time()

    def _prune_old_failures(self, ip: str, now: Optional[float] = None):
        now = self._now() if now is None else now
        window_start = now - self.findtime
        events = self._failures.get(ip, [])
        if events:
            self._failures[ip] = [t for t in events if t >= window_start]
            if not self._failures[ip]:
                self._failures.pop(ip, None)

    def process_line(self, line: str, timestamp: Optional[float] = None) -> Dict[str, Any]:
        """
        Process a single log line.

        Uses the jail's filter to detect a failure. If matched, records the failure for the IP
        found either through regex groups or by scanning the line.

        Returns dict:
          - matched: bool
          - ip: str|None
          - ban_triggered: bool
          - pattern: str|None
        """
        ts = self._now() if timestamp is None else timestamp

        r = self.filter.match_line(line)
        ip = r.get("ip") or searchIP(line)
        matched = bool(r.get("matched"))

        ban_triggered = False
        if matched and ip:
            # Record failure
            self._failures.setdefault(ip, []).append(ts)
            # Prune old failures outside findtime
            self._prune_old_failures(ip, now=ts)

            if self.should_ban(ip, now=ts):
                # In this minimal subset, ban means recording in-memory, no side effects
                self.ban(ip, now=ts)
                ban_triggered = True

        return {"matched": matched, "ip": ip, "ban_triggered": ban_triggered, "pattern": r.get("pattern")}

    def get_fail_count(self, ip: str, now: Optional[float] = None) -> int:
        now = self._now() if now is None else now
        self._prune_old_failures(ip, now=now)
        return len(self._failures.get(ip, []))

    def should_ban(self, ip: str, now: Optional[float] = None) -> bool:
        """
        True if failures within findtime for the IP are >= maxretry.
        """
        count = self.get_fail_count(ip, now=now)
        return count >= self.maxretry

    def ban(self, ip: str, now: Optional[float] = None) -> None:
        """
        Record that IP is banned until now + bantime. No firewall changes are made.
        """
        now = self._now() if now is None else now
        self._banned[ip] = now + self.bantime

    def is_banned(self, ip: str, now: Optional[float] = None) -> bool:
        now = self._now() if now is None else now
        until = self._banned.get(ip)
        if until is None:
            return False
        if until <= now:
            # expired
            self._banned.pop(ip, None)
            return False
        return True

    def unban_expired(self, now: Optional[float] = None) -> None:
        """
        Remove expired bans.
        """
        now = self._now() if now is None else now
        expired = [ip for ip, until in self._banned.items() if until <= now]
        for ip in expired:
            self._banned.pop(ip, None)

    def get_status(self, now: Optional[float] = None) -> Dict[str, Any]:
        """
        Return a minimal status dictionary for the jail.
        """
        now = self._now() if now is None else now
        self.unban_expired(now=now)
        return {
            "name": self.name,
            "maxretry": self.maxretry,
            "findtime": self.findtime,
            "bantime": self.bantime,
            "failures": {ip: self.get_fail_count(ip, now=now) for ip in self._failures.keys()},
            "banned": {ip: until for ip, until in self._banned.items()},
        }

    @classmethod
    def from_config_section(cls, name: str, section: Dict[str, Any]) -> "Jail":
        """
        Create a Jail from a dict-like section.
        Recognized keys: maxretry, findtime, bantime, failregex (list or str), ignoreregex (list or str)

        This helper allows offline jail initialization based on configuration data.
        """
        maxretry = int(section.get("maxretry", 5))
        findtime = int(section.get("findtime", 600))
        bantime = int(section.get("bantime", 600))
        failregex = section.get("failregex", [])
        if isinstance(failregex, str):
            failregex = [failregex]
        ignoreregex = section.get("ignoreregex", [])
        if isinstance(ignoreregex, str):
            ignoreregex = [ignoreregex]

        filt = Filter(name=name, failregex=failregex, ignoreregex=ignoreregex)
        return cls(name=name, filter=filt, maxretry=maxretry, findtime=findtime, bantime=bantime)