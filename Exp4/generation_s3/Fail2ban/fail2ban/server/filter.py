from __future__ import annotations

import ipaddress
import re
from typing import List, Optional


# Conservative candidate extractors; final validation uses ipaddress.
_IPV4_CANDIDATE_RE = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
# IPv6 is tricky; accept reasonably broad tokens containing ":" and hex, then validate.
_IPV6_CANDIDATE_RE = re.compile(r"(?<![\w:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![\w:])")


def _coerce_str(value) -> str:
    try:
        return value if isinstance(value, str) else str(value)
    except Exception:
        return ""


def _strip_brackets(token: str) -> str:
    # Support "[::1]" style by stripping single surrounding brackets.
    if len(token) >= 2 and token[0] == "[" and token[-1] == "]":
        return token[1:-1]
    return token


def isValidIP(ip: str) -> bool:
    """
    Return True if ip is a valid textual IPv4 or IPv6 address, else False.
    Never raises for weird inputs.
    """
    s = _coerce_str(ip).strip()
    if not s:
        return False

    s = _strip_brackets(s)

    # Reject common port suffixes explicitly; ipaddress doesn't accept them anyway
    # but this keeps behavior predictable.
    if s.count(":") == 1 and "." in s and s.rsplit(":", 1)[-1].isdigit():
        # e.g. "1.2.3.4:22"
        return False

    try:
        ipaddress.ip_address(s)
        return True
    except Exception:
        return False


def findAllIP(text: str) -> List[str]:
    """
    Return all valid IPs found in text (IPv4 and IPv6), in order of appearance.
    May include duplicates.
    """
    s = _coerce_str(text)
    if not s:
        return []

    candidates: List[tuple[int, str]] = []

    for m in _IPV4_CANDIDATE_RE.finditer(s):
        candidates.append((m.start(), m.group(0)))

    for m in _IPV6_CANDIDATE_RE.finditer(s):
        tok = m.group(0)
        # Avoid treating a pure "::::" style junk as candidate; still validate.
        candidates.append((m.start(), tok))

    candidates.sort(key=lambda t: t[0])

    out: List[str] = []
    for _, tok in candidates:
        tok2 = _strip_brackets(tok)
        if isValidIP(tok2):
            out.append(tok2)
    return out


def searchIP(text: str) -> Optional[str]:
    """Return the first valid IP found in text, else None."""
    ips = findAllIP(text)
    return ips[0] if ips else None


class RegexFilter:
    """
    Minimal regex-based filter.

    - failregex: list of patterns that indicate a failure line.
    - ignoreregex: list of patterns that suppress matches.
    - use_dns is accepted for compatibility but never used (no DNS/network).
    """

    def __init__(
        self,
        failregex: Optional[List[str]] = None,
        ignoreregex: Optional[List[str]] = None,
        *,
        use_dns: bool = False,
    ):
        self._use_dns = bool(use_dns)
        self._fail_patterns: List[re.Pattern] = []
        self._ignore_patterns: List[re.Pattern] = []
        self._fail_sources: List[str] = []
        self._ignore_sources: List[str] = []

        if failregex:
            for p in failregex:
                self.addFailRegex(p)
        if ignoreregex:
            for p in ignoreregex:
                self.addIgnoreRegex(p)

    def addFailRegex(self, pattern: str) -> None:
        try:
            c = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid failregex pattern: {pattern!r}: {e}") from e
        self._fail_patterns.append(c)
        self._fail_sources.append(pattern)

    def addIgnoreRegex(self, pattern: str) -> None:
        try:
            c = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid ignoreregex pattern: {pattern!r}: {e}") from e
        self._ignore_patterns.append(c)
        self._ignore_sources.append(pattern)

    def getFailRegex(self) -> List[str]:
        return list(self._fail_sources)

    def getIgnoreRegex(self) -> List[str]:
        return list(self._ignore_sources)

    def matchLine(self, line: str) -> List[str]:
        """
        Returns offending IPs extracted from the line if:
          - no ignore regex matches; and
          - at least one failregex matches.

        IP extraction is performed by scanning the line for valid IPs (no capture group required).
        """
        s = _coerce_str(line)

        if not self._fail_patterns:
            return []

        for ign in self._ignore_patterns:
            if ign.search(s):
                return []

        for fr in self._fail_patterns:
            if fr.search(s):
                return findAllIP(s)

        return []