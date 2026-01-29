from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional

from .actions import Actions
from .filter import FailRegex
from .ticket import Ticket

@dataclass(slots=True)
class _BanInfo:
    time: float
    reason: str

class Jail:
    """
    Minimal jail:
    - Evaluates a set of failregex patterns (and optional ignoreregex)
    - Tracks failures per IP within findtime
    - "Bans" by recording in memory via Actions (no system modifications)
    """
    def __init__(
        self,
        name: str,
        filter_regex: str | None = None,
        failregex: list[str] | None = None,
        ignoreregex: list[str] | None = None,
        maxretry: int = 3,
        findtime: int = 600,
        bantime: int = 600,
    ):
        self.name = name
        if filter_regex and not failregex:
            failregex = [filter_regex]
        self.failregex = list(failregex or [])
        self.ignoreregex = list(ignoreregex or [])
        if not self.failregex:
            raise ValueError("Jail requires failregex (or filter_regex)")

        if maxretry < 1:
            raise ValueError("maxretry must be >= 1")
        if findtime < 0:
            raise ValueError("findtime must be >= 0")

        self.maxretry = int(maxretry)
        self.findtime = int(findtime)
        self.bantime = int(bantime)

        self.filter = FailRegex(self.failregex, self.ignoreregex)
        self.actions = Actions(self.name)

        self._failures: dict[str, Deque[float]] = {}
        self._bans: dict[str, _BanInfo] = {}
        self._stats = {"lines": 0, "matches": 0, "ignored": 0, "bans": 0}

        # Optional config attribute used by configreader; no operational effect here.
        self.enabled: bool = True

    def reset(self) -> None:
        self._failures.clear()
        self._bans.clear()
        self._stats = {"lines": 0, "matches": 0, "ignored": 0, "bans": 0}
        self.actions = Actions(self.name)

    def _prune_failures(self, ip: str, now: float) -> None:
        if self.findtime <= 0:
            return
        dq = self._failures.get(ip)
        if not dq:
            return
        cutoff = now - self.findtime
        while dq and dq[0] < cutoff:
            dq.popleft()
        if not dq:
            self._failures.pop(ip, None)

    def _expire_bans(self, now: float) -> None:
        if self.bantime <= 0:
            return
        expired = []
        for ip, info in self._bans.items():
            if now >= info.time + self.bantime:
                expired.append(ip)
        for ip in expired:
            self._bans.pop(ip, None)
            self.actions.unban(ip)

    def add_log_line(self, line: str, now: float | None = None) -> list[str]:
        if now is None:
            # Deterministic tests pass now; if not provided, use monotonic-ish time.
            import time
            now = time.time()

        self._stats["lines"] += 1
        self._expire_bans(now)

        # Ignore handling is implemented in FailRegex.match_line by returning None.
        info = self.filter.match_line(line)
        if info is None:
            # Could be ignored or non-match. We can't distinguish precisely without
            # re-checking ignore patterns; keep it simple: treat as non-match.
            return []

        self._stats["matches"] += 1
        ip = info.get("ip")
        if not ip:
            return []

        # If already banned, do not keep counting (typical behavior).
        if ip in self._bans:
            return []

        dq = self._failures.setdefault(ip, deque())
        dq.append(float(now))
        self._prune_failures(ip, float(now))

        if len(dq) >= self.maxretry:
            reason = f"maxretry reached ({len(dq)}/{self.maxretry})"
            self._bans[ip] = _BanInfo(time=float(now), reason=reason)
            self.actions.ban(ip, reason=reason)
            self._stats["bans"] += 1
            return [ip]

        return []

    def process_lines(self, lines: list[str], now: float | None = None) -> dict:
        banned: list[str] = []
        matches = 0
        for line in lines:
            before_matches = self._stats["matches"]
            banned.extend(self.add_log_line(line, now=now))
            if self._stats["matches"] > before_matches:
                matches += 1
        out = dict(self._stats)
        out["banned"] = set(self.get_banned())
        out["newly_banned"] = banned
        out["matches_in_call"] = matches
        return out

    def get_banned(self) -> set[str]:
        # Ensure any time-based expiry when caller queries and provides no now.
        # Here, avoid implicit time; just return current state.
        return set(self._bans.keys())

    def ticket_from_line(self, line: str, now: float | None = None) -> Optional[Ticket]:
        if now is None:
            import time
            now = time.time()
        info = self.filter.match_line(line)
        if not info or not info.get("ip"):
            return None
        return Ticket(ip=info["ip"], time=float(now), line=line, pattern=info["pattern"])