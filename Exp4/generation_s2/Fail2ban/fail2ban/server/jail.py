from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Iterable, Tuple
import time
import re

from . import filter as f2bfilter


@dataclass
class JailStatus:
    name: str
    enabled: bool
    bantime: int
    findtime: int
    maxretry: int
    banned: List[str] = field(default_factory=list)
    failures: Dict[str, List[float]] = field(default_factory=dict)


class Jail:
    """
    Minimal Jail object coordinating filter regex matching and in-memory bans.

    This is a safe, offline-only implementation:
    - No firewall operations
    - No daemon threads
    - Ban list is in-memory
    """

    def __init__(
        self,
        name: str,
        failregex: Optional[Iterable[str]] = None,
        ignoreregex: Optional[Iterable[str]] = None,
        maxretry: int = 5,
        findtime: int = 600,
        bantime: int = 600,
        enabled: bool = True,
    ):
        self.name = name
        self.enabled = bool(enabled)
        self.maxretry = int(maxretry)
        self.findtime = int(findtime)
        self.bantime = int(bantime)

        self._failregex_raw = list(failregex or [])
        self._ignoreregex_raw = list(ignoreregex or [])

        self._failregex = f2bfilter.parse_failregexes(self._failregex_raw)
        self._ignoreregex = f2bfilter.parse_failregexes(self._ignoreregex_raw)

        self._failures: Dict[str, List[float]] = {}
        self._banned_until: Dict[str, float] = {}

    def setFailRegex(self, patterns: Iterable[str]) -> None:
        self._failregex_raw = list(patterns)
        self._failregex = f2bfilter.parse_failregexes(self._failregex_raw)

    def setIgnoreRegex(self, patterns: Iterable[str]) -> None:
        self._ignoreregex_raw = list(patterns)
        self._ignoreregex = f2bfilter.parse_failregexes(self._ignoreregex_raw)

    def _is_ignored(self, line: str) -> bool:
        for pat in self._ignoreregex:
            if pat.search(line):
                return True
        return False

    def _cleanup_old_failures(self, host: str, now: float) -> None:
        window_start = now - self.findtime
        times = self._failures.get(host, [])
        times = [t for t in times if t >= window_start]
        if times:
            self._failures[host] = times
        else:
            self._failures.pop(host, None)

    def _is_banned(self, host: str, now: float) -> bool:
        until = self._banned_until.get(host)
        if until is None:
            return False
        if now >= until:
            self._banned_until.pop(host, None)
            return False
        return True

    def unban(self, host: str) -> bool:
        """Remove host from ban list. Returns True if it was banned."""
        return self._banned_until.pop(host, None) is not None

    def ban(self, host: str, now: Optional[float] = None) -> None:
        """Ban host in-memory until now + bantime."""
        if not f2bfilter.isValidIP(host):
            return
        if now is None:
            now = time.time()
        self._banned_until[host] = float(now) + self.bantime

    def processLine(self, line: str, now: Optional[float] = None) -> Optional[str]:
        """
        Process a single log line. Return banned IP if ban occurred, else None.

        Line matching:
        - Ignore if ignoreregex matches.
        - If any failregex matches, extract host and count failure.
        """
        if not self.enabled:
            return None
        if not line:
            return None
        if now is None:
            now = time.time()

        if self._is_ignored(line):
            return None

        matches = f2bfilter.match_failregexes(line, self._failregex)
        if not matches:
            return None

        for _, m in matches:
            host = f2bfilter.extract_host_from_match(m)
            if not host:
                continue
            if not f2bfilter.isValidIP(host):
                continue

            if self._is_banned(host, now):
                return None

            self._cleanup_old_failures(host, now)
            self._failures.setdefault(host, []).append(float(now))
            self._cleanup_old_failures(host, now)

            if len(self._failures.get(host, [])) >= self.maxretry:
                self.ban(host, now=now)
                return host

        return None

    def status(self) -> JailStatus:
        now = time.time()
        banned = []
        for host in list(self._banned_until.keys()):
            if self._is_banned(host, now):
                banned.append(host)
        # Present failures after cleanup
        failures: Dict[str, List[float]] = {}
        for host, times in list(self._failures.items()):
            self._cleanup_old_failures(host, now)
        for host, times in self._failures.items():
            failures[host] = list(times)

        return JailStatus(
            name=self.name,
            enabled=self.enabled,
            bantime=self.bantime,
            findtime=self.findtime,
            maxretry=self.maxretry,
            banned=sorted(banned),
            failures=failures,
        )