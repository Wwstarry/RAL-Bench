from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .filter import FailRegex


@dataclass
class Jail:
    """
    Minimal jail coordinating a filter (regex) and ban bookkeeping.

    This implementation is offline-only:
    - It never touches firewall rules.
    - It only tracks which IPs would be banned based on maxretry.
    """

    name: str
    failregex: List[str]
    maxretry: int = 3

    _filter: FailRegex = field(init=False, repr=False)
    _failures: Dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _banned: Set[str] = field(default_factory=set, init=False, repr=False)
    _events: List[Tuple[str, str]] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        if not self.name or not isinstance(self.name, str):
            raise ValueError("jail name must be a non-empty string")
        if not isinstance(self.maxretry, int) or self.maxretry < 1:
            raise ValueError("maxretry must be >= 1")
        self._filter = FailRegex(self.failregex)

    def process_line(self, line: str) -> Optional[str]:
        """
        Process a single log line. If it matches a failregex and results in a ban,
        returns the banned IP; otherwise None.
        """
        res = self._filter.match_line(line)
        if not res:
            return None
        ip, _m = res
        if ip in self._banned:
            self._events.append(("match", ip))
            return None
        self._failures[ip] = self._failures.get(ip, 0) + 1
        self._events.append(("failure", ip))
        if self._failures[ip] >= self.maxretry:
            self._banned.add(ip)
            self._events.append(("ban", ip))
            return ip
        return None

    def process_lines(self, lines: List[str]) -> List[str]:
        banned_now = []
        for line in lines:
            ip = self.process_line(line)
            if ip:
                banned_now.append(ip)
        return banned_now

    def getFailures(self, ip: str) -> int:
        return int(self._failures.get(ip, 0))

    def isBanned(self, ip: str) -> bool:
        return ip in self._banned

    def getBanned(self) -> List[str]:
        return sorted(self._banned)

    def reset(self):
        self._failures.clear()
        self._banned.clear()
        self._events.clear()

    def getEvents(self) -> List[Tuple[str, str]]:
        return list(self._events)