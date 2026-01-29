"""
fail2ban.server.jail
====================

This is a drastically simplified re-implementation of Fail2Ban's ``Jail`` class.
It keeps the public surface small yet useful for unit-testing purposes.

Major omissions:
    • No daemonisation, threading or persistence.
    • No real firewall interaction (obviously – security reasons).
    • No comprehensive configuration handling.

Implemented Features
--------------------
    • Parsing/holding core configuration parameters that the tests rely on.
    • Feeding log lines and matching against *failregex* patterns.
    • Tracking per-IP failure counters with ``findtime`` / ``maxretry`` semantics.
    • Soft-ban bookkeeping (``is_banned`` / ``get_banned_ips``).
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Iterable, List, Dict

from .filter import searchIP, isValidIP


class Jail:
    """
    Minimal jail implementation.
    """

    def __init__(
        self,
        name: str,
        failregex: Iterable[str] | str,
        *,
        ignoreip: Iterable[str] | None = None,
        maxretry: int = 5,
        findtime: int | float = 600,
        bantime: int | float = 600,
    ) -> None:
        """
        Parameters
        ----------
        name:
            Arbitrary identifier. Used only for representation.
        failregex:
            List of (or single) regular-expression strings which indicate an
            authentication failure when matched in a log line.
        ignoreip:
            Iterable of IP addresses never to be banned.
        maxretry:
            How many failures inside the *findtime* window will trigger a ban.
        findtime:
            Window length (seconds) in which *maxretry* failures cause a ban.
        bantime:
            Duration (seconds) an offending IP is kept in the *banned* list.
        """
        self.name: str = name
        if isinstance(failregex, (str, bytes)):
            failregex = [failregex]  # type: ignore[assignment]
        self._failregex: List[re.Pattern[str]] = [re.compile(fr) for fr in failregex]

        self.ignoreip = {ip for ip in (ignoreip or []) if isValidIP(ip)}
        self.maxretry = maxretry
        self.findtime = float(findtime)
        self.bantime = float(bantime)

        # Failure history: ip -> List[timestamps]
        self._failures: Dict[str, List[float]] = {}
        # Active bans: ip -> ban_expiry_ts
        self._banned: Dict[str, float] = {}

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _now() -> float:
        return time.time()

    # ------------------------------------------------------------------ actions

    def process_line(self, line: str, *, timestamp: float | None = None) -> None:
        """
        Process a *line* from a log file.

        When the line matches one of the failure patterns AND contains an IP
        address, the internal failure counter for that IP is updated and a ban
        might be triggered.
        """
        now = self._now() if timestamp is None else float(timestamp)
        self._expire(now)

        # Quick exit: check whether the IP we find (if any) is already banned.
        ip = searchIP(line)
        if not ip or not isValidIP(ip) or ip in self.ignoreip:
            return

        # See if the line indicates a failure.
        if not any(r.search(line) for r in self._failregex):
            return

        # Record the failure.
        self._failures.setdefault(ip, []).append(now)
        # Only keep those still inside the findtime window.
        self._failures[ip] = [t for t in self._failures[ip] if now - t <= self.findtime]

        # Evaluate whether the IP should be banned.
        if len(self._failures[ip]) >= self.maxretry:
            self._ban_ip(ip, now)

    # ------------------------------------------------------------------ banning

    def _ban_ip(self, ip: str, now: float) -> None:
        """
        Register *ip* as banned until *now + bantime*.
        """
        # Prevent banning ignored IPs (should not happen if ignoreip handled).
        if ip in self.ignoreip:
            return
        self._banned[ip] = now + self.bantime
        # Purge failure history – start fresh after ban lifts.
        self._failures.pop(ip, None)

    def _expire(self, now: float | None = None) -> None:
        """
        Clean-up failure history and remove expired bans.
        """
        if now is None:
            now = self._now()

        # Remove old failures outside findtime window.
        for ip, times in list(self._failures.items()):
            self._failures[ip] = [t for t in times if now - t <= self.findtime]
            if not self._failures[ip]:
                self._failures.pop(ip, None)

        # Remove expired bans.
        for ip, expiry in list(self._banned.items()):
            if now >= expiry:
                self._banned.pop(ip, None)

    # ------------------------------------------------------------------ queries

    def is_banned(self, ip: str) -> bool:
        """
        Return *True* if *ip* is currently banned.
        """
        self._expire()
        return ip in self._banned

    def get_banned_ips(self) -> List[str]:
        """
        Return **active** banned IPs.
        """
        self._expire()
        return sorted(self._banned.keys())

    # ------------------------------------------------------------------ misc

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Jail {self.name!r}: banned={len(self._banned)} "
            f"maxretry={self.maxretry} findtime={self.findtime}s bantime={self.bantime}s>"
        )

    # ------------------------------------------------------------------ utility constructors

    @classmethod
    def from_config_file(cls, path: str | Path) -> "Jail":
        """
        Extremely small parser able to read INI-like *jail.conf* fragments:

            [sshd]
            enabled  = true
            maxretry = 3
            findtime = 600
            bantime  = 1800
            failregex = ^%(__prefix_line)sFailed password.* from <HOST>

        Only the first section is interpreted and only a handful of keys are used.
        """
        import configparser

        parser = configparser.ConfigParser(interpolation=None)
        with open(path, encoding="utf-8") as fh:
            parser.read_file(fh)

        if not parser.sections():
            raise ValueError("no sections found in configuration")

        section = parser.sections()[0]
        cfg = parser[section]

        failregex = [line.strip() for line in cfg.get("failregex", "").splitlines() if line.strip()]
        if not failregex:
            raise ValueError("failregex missing in config")

        return cls(
            name=section,
            failregex=failregex,
            ignoreip=[ip.strip() for ip in cfg.get("ignoreip", "").split()],
            maxretry=cfg.getint("maxretry", fallback=5),
            findtime=cfg.getint("findtime", fallback=600),
            bantime=cfg.getint("bantime", fallback=600),
        )