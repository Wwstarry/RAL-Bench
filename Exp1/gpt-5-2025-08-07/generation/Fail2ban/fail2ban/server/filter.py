"""
Minimal filter utilities for a safe subset of Fail2Ban.

Provides:
- isValidIP(ip): bool
- searchIP(text): first valid IP found or None
- searchAllIPs(text): list of valid IPs found
- Filter class: manage fail/ignore regex and match lines, extracting IPs.

This module avoids any system modifications and is safe for offline use.
"""
import re
import ipaddress
from typing import Optional, List, Tuple, Dict, Any


# Precompiled IPv4 candidate pattern (valid ranges 0-255)
_IPV4_CANDIDATE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b"
)

# Loose tokenization for IPv6 candidates; actual validation via ipaddress
_TOKENIZER = re.compile(r"[0-9A-Fa-f:.]+")

# Fail2Ban-style HOST placeholder. We include a named 'ip' group.
# This supports IPv4 and a loose IPv6 form validated later by ipaddress in Filter when needed.
HOST_PLACEHOLDER_REGEX = (
    r"(?P<ip>"
    r"(?:\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b)"
    r"|"
    r"(?:\b(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}\b)"
    r")"
)


def isValidIP(ip: str) -> bool:
    """
    Return True if the string represents a valid IPv4 or IPv6 address.
    """
    if not isinstance(ip, str) or not ip:
        return False
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def searchAllIPs(text: str) -> List[str]:
    """
    Return list of valid IP addresses (IPv4/IPv6) found in the given text.
    Order is: all valid IPv4 matches first (left-to-right), then IPv6 validated tokens.
    """
    if not text:
        return []

    ips: List[str] = []

    # Prefer IPv4 candidates via strict regex
    for m in _IPV4_CANDIDATE.finditer(text):
        candidate = m.group(0)
        try:
            ipaddress.IPv4Address(candidate)
            ips.append(candidate)
        except ValueError:
            # Not a valid IPv4; skip
            pass

    # Tokenize potential IPv6 candidates and validate
    for token in _TOKENIZER.findall(text):
        # Skip obvious IPv4 which we already captured
        if "." in token and ":" not in token:
            continue
        # Clean common brackets or punctuation
        cleaned = token.strip("[](),;")
        if not cleaned or cleaned in ips:
            continue
        try:
            ipaddress.ip_address(cleaned)
            # Check not already present (to avoid duplicates)
            if cleaned not in ips:
                ips.append(cleaned)
        except ValueError:
            continue

    return ips


def searchIP(text: str) -> Optional[str]:
    """
    Return first valid IP (IPv4/IPv6) found in the given text, or None.
    """
    ips = searchAllIPs(text)
    return ips[0] if ips else None


def _expand_placeholders(pattern: str) -> str:
    """
    Replace Fail2Ban placeholders with local equivalents.
    Currently supports <HOST>.
    """
    if not isinstance(pattern, str):
        return pattern
    return pattern.replace("<HOST>", HOST_PLACEHOLDER_REGEX)


class Filter:
    """
    Minimal representation of a Fail2Ban filter.

    - failregex: list of patterns considered suspicious (authentication failure, etc).
    - ignoreregex: patterns to ignore (whitelisting).

    match_line(line) returns a dictionary with:
      - matched: bool
      - ip: str|None
      - match: re.Match|None
      - pattern: str (pattern used)
    """

    def __init__(self, name: str = "generic", failregex: Optional[List[str]] = None, ignoreregex: Optional[List[str]] = None):
        self.name = name
        self.failregex: List[Tuple[str, re.Pattern]] = []
        self.ignoreregex: List[Tuple[str, re.Pattern]] = []
        if failregex:
            for p in failregex:
                self.add_failregex(p)
        if ignoreregex:
            for p in ignoreregex:
                self.add_ignoreregex(p)

    def add_failregex(self, pattern: str):
        expanded = _expand_placeholders(pattern)
        try:
            compiled = re.compile(expanded)
        except re.error as e:
            raise ValueError(f"Invalid failregex pattern: {pattern!r} ({e})")
        self.failregex.append((pattern, compiled))

    def add_ignoreregex(self, pattern: str):
        expanded = _expand_placeholders(pattern)
        try:
            compiled = re.compile(expanded)
        except re.error as e:
            raise ValueError(f"Invalid ignoreregex pattern: {pattern!r} ({e})")
        self.ignoreregex.append((pattern, compiled))

    def _is_ignored(self, line: str) -> bool:
        for _, ign in self.ignoreregex:
            if ign.search(line):
                return True
        return False

    def match_line(self, line: str) -> Dict[str, Any]:
        """
        Try to match the line against failregex patterns.

        If any failregex matches and ignoreregex does not, return data including ip if can be extracted.
        IP resolution order:
          1) Named group 'ip' or 'host' in match, if present and valid.
          2) searchIP() on the entire line.

        Returns dict: {'matched': bool, 'ip': str|None, 'match': re.Match|None, 'pattern': str|None}
        """
        result = {"matched": False, "ip": None, "match": None, "pattern": None}
        if not isinstance(line, str):
            return result

        if self._is_ignored(line):
            return result

        for original, rgx in self.failregex:
            m = rgx.search(line)
            if m:
                result["matched"] = True
                result["match"] = m
                result["pattern"] = original

                # Try named groups first
                ip = None
                for key in ("ip", "host", "HOST"):
                    if key in m.groupdict():
                        ip = m.group(key)
                        break

                if ip and isValidIP(ip):
                    result["ip"] = ip
                    return result

                # fallback to scanning the entire line
                ip2 = searchIP(line)
                if ip2:
                    result["ip"] = ip2

                return result

        return result