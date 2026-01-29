import ipaddress
import re
from typing import Optional, List, Tuple, Iterable


_IP4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b"
)
# A deliberately permissive IPv6 candidate matcher; validated via ipaddress afterwards.
_IP6_CANDIDATE_RE = re.compile(r"\b[0-9A-Fa-f:]{2,}\b")


def isValidIP(ip: str) -> bool:
    """Return True if ip is a valid IPv4 or IPv6 address."""
    if not ip:
        return False
    try:
        ipaddress.ip_address(ip.strip())
        return True
    except ValueError:
        return False


def _extract_ipv6_candidates(text: str) -> Iterable[str]:
    # Avoid matching things like "dead:beef" that are not valid IPs; ipaddress will filter.
    for m in _IP6_CANDIDATE_RE.finditer(text):
        cand = m.group(0)
        if ":" not in cand:
            continue
        yield cand


def searchIP(text: str) -> Optional[str]:
    """
    Search for first IP address in a string and return it, else None.

    Matches IPv4 using strict regex; IPv6 is matched more loosely and validated.
    """
    if not text:
        return None

    m4 = _IP4_RE.search(text)
    if m4:
        return m4.group(0)

    for cand in _extract_ipv6_candidates(text):
        if isValidIP(cand):
            return cand
    return None


def findAllIPs(text: str) -> List[str]:
    """Return all unique IPs found in text, in occurrence order."""
    if not text:
        return []
    out: List[str] = []
    seen = set()

    for m in _IP4_RE.finditer(text):
        ip = m.group(0)
        if ip not in seen:
            seen.add(ip)
            out.append(ip)

    for cand in _extract_ipv6_candidates(text):
        if isValidIP(cand) and cand not in seen:
            seen.add(cand)
            out.append(cand)

    return out


def _compile_regex(pattern: str) -> re.Pattern:
    # Fail2Ban regexes often use (?P<host>...) etc. We allow standard Python regex.
    # Multiline not default; callers can embed flags like (?i).
    return re.compile(pattern)


def parse_failregexes(patterns: List[str]) -> List[re.Pattern]:
    return [_compile_regex(p) for p in patterns]


def match_failregexes(line: str, patterns: List[re.Pattern]) -> List[Tuple[re.Pattern, re.Match]]:
    """Return list of (pattern, match) for all patterns that match the line."""
    matches = []
    for pat in patterns:
        m = pat.search(line)
        if m:
            matches.append((pat, m))
    return matches


def extract_host_from_match(m: "re.Match") -> Optional[str]:
    """
    Extract host/IP from match groups.

    Preferred group: 'host' (Fail2Ban convention). Fallback to first valid IP in match text.
    """
    try:
        gd = m.groupdict()
    except Exception:
        gd = {}

    host = gd.get("host")
    if host and isValidIP(host):
        return host

    # Some regexes use 'ip' group; accept it too.
    ip = gd.get("ip")
    if ip and isValidIP(ip):
        return ip

    return searchIP(m.group(0))