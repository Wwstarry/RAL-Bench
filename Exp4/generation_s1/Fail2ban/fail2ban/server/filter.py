from __future__ import annotations

import ipaddress
import re
from typing import Optional

# Conservative patterns intended for log extraction (not full RFC parsing).
_IPV4_RE = re.compile(
    r"(?<![\d.])"
    r"(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1?\d?\d)"
    r"(?![\d.])"
)

# For IPv6, use a broad-but-bounded token then validate via ipaddress.
# We avoid matching very short ":" sequences by requiring at least two colons.
_IPV6_TOKEN_RE = re.compile(
    r"(?<![0-9A-Fa-f:])"
    r"([0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,7})"
    r"(?![0-9A-Fa-f:])"
)

_BRACKETED_RE = re.compile(r"\[([^\]]+)\](?::\d+)?")

def isValidIP(ip: str) -> bool:
    """
    Validate plain IPv4/IPv6 address string.
    Rejects:
      - bracketed forms like "[1.2.3.4]"
      - CIDR like "1.2.3.4/24"
      - zone ids like "fe80::1%eth0"
    """
    if not isinstance(ip, str):
        return False
    ip = ip.strip()
    if not ip or "[" in ip or "]" in ip or "/" in ip or "%" in ip:
        return False
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def _strip_brackets_and_port(text: str) -> str:
    m = _BRACKETED_RE.search(text)
    if not m:
        return text
    return m.group(1)

def searchIP(text: str) -> Optional[str]:
    """
    Extract first valid IPv4 or IPv6 address from text.
    Supports:
      - "... from 1.2.3.4 ..."
      - "... [1.2.3.4] ..."
      - "... client [2001:db8::1]:1234 ..."
    """
    if not text:
        return None

    # Prefer bracketed forms first (common for IPv6).
    bracket = _strip_brackets_and_port(text)
    if bracket != text and isValidIP(bracket):
        return bracket

    m4 = _IPV4_RE.search(text)
    if m4:
        ip = m4.group(0)
        if isValidIP(ip):
            return ip

    m6 = _IPV6_TOKEN_RE.search(text)
    if m6:
        token = m6.group(1)
        if isValidIP(token):
            return token

    return None

def compile_failregex(patterns: list[str]) -> list[re.Pattern]:
    compiled: list[re.Pattern] = []
    for p in patterns:
        try:
            compiled.append(re.compile(p))
        except re.error as e:
            raise ValueError(f"Invalid failregex pattern: {p!r}: {e}") from e
    return compiled

def compile_ignoreregex(patterns: list[str]) -> list[re.Pattern]:
    compiled: list[re.Pattern] = []
    for p in patterns:
        try:
            compiled.append(re.compile(p))
        except re.error as e:
            raise ValueError(f"Invalid ignoreregex pattern: {p!r}: {e}") from e
    return compiled

class FailRegex:
    def __init__(self, patterns: list[str], ignoreregex: list[str] | None = None):
        if not patterns:
            raise ValueError("At least one failregex pattern is required")
        self.patterns_raw = list(patterns)
        self.ignoreregex_raw = list(ignoreregex or [])
        self.fail = compile_failregex(self.patterns_raw)
        self.ignore = compile_ignoreregex(self.ignoreregex_raw)

    def find_ip(self, matchobj: re.Match, line: str) -> Optional[str]:
        gd = matchobj.groupdict() if matchobj else {}
        for key in ("ip", "host"):
            if key in gd and gd[key]:
                candidate = gd[key].strip()
                # Some logs capture host:port or [ip]:port; try to normalize.
                candidate2 = _strip_brackets_and_port(candidate)
                if isValidIP(candidate2):
                    return candidate2
        # Fallback: search whole line.
        return searchIP(line)

    def match_line(self, line: str) -> Optional[dict]:
        if line is None:
            return None

        # If any ignore matches, treat as ignored even if failregex matches.
        for ign in self.ignore:
            if ign.search(line):
                return None

        for raw, cre in zip(self.patterns_raw, self.fail):
            m = cre.search(line)
            if not m:
                continue
            ip = self.find_ip(m, line)
            return {"pattern": raw, "ip": ip, "match": m}
        return None