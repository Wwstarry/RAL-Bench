import ipaddress
import re
from typing import List, Optional, Tuple


_IP_BRACKET_RE = re.compile(r"^\[(?P<ip>[^]]+)\]$")


def isValidIP(value: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    value = value.strip()
    m = _IP_BRACKET_RE.match(value)
    if m:
        value = m.group("ip")
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def normalize_ip(value: str) -> Optional[str]:
    if not isinstance(value, str) or not value:
        return None
    value = value.strip()
    m = _IP_BRACKET_RE.match(value)
    if m:
        value = m.group("ip")
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def searchIP(text: str) -> Optional[str]:
    """
    Search for an IP address in text. Returns the first IP found, normalized,
    or None if not found.

    This is intentionally conservative and safe; it doesn't attempt to parse
    exotic formats beyond plain IPv4/IPv6 tokens (optionally in [brackets]).
    """
    if not isinstance(text, str) or not text:
        return None

    # Candidate tokens: bracketed or plain, separated by whitespace/punct.
    # We'll scan tokens and validate with ipaddress.
    # Include ':' for ipv6, '.' for ipv4, hex digits, and brackets.
    for tok in re.findall(r"\[?[0-9A-Fa-f:.]{2,}\]?", text):
        ip = normalize_ip(tok)
        if ip is not None:
            return ip
    return None


def findAllIPs(text: str) -> List[str]:
    if not isinstance(text, str) or not text:
        return []
    found = []
    seen = set()
    for tok in re.findall(r"\[?[0-9A-Fa-f:.]{2,}\]?", text):
        ip = normalize_ip(tok)
        if ip is not None and ip not in seen:
            seen.add(ip)
            found.append(ip)
    return found


class FailRegex:
    """
    Minimal Fail2Ban-like failregex evaluator.
    It compiles one or multiple regex patterns and extracts IPs using either:
      - a named group 'ip' if present; else
      - fail2ban.server.filter.searchIP over the match text; else
      - entire line search.
    """

    def __init__(self, patterns):
        if isinstance(patterns, str):
            patterns = [patterns]
        if not patterns:
            raise ValueError("patterns must not be empty")
        self.patterns = list(patterns)
        self._compiled = []
        for p in self.patterns:
            if not isinstance(p, str) or not p.strip():
                raise ValueError("invalid pattern")
            self._compiled.append(re.compile(p))

    def match_line(self, line: str) -> Optional[Tuple[str, re.Match]]:
        for cre in self._compiled:
            m = cre.search(line)
            if not m:
                continue
            ip = None
            if "ip" in cre.groupindex:
                ip = normalize_ip(m.group("ip"))
            if ip is None:
                ip = searchIP(m.group(0)) or searchIP(line)
            if ip is None:
                return None
            return ip, m
        return None