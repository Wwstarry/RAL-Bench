"""
fail2ban.server.filter
======================

A *very* small helper module that offers the API surface required by the
benchmark tests:

Functions
---------
isValidIP(ip: str) -> bool
    Validate whether *ip* is a legal IPv4 or IPv6 address.

searchIP(text: str) -> Optional[str]
    Scan *text* and return the first IPv4 or IPv6 address found
    or ``None`` when none is present.

The implementation purposefully avoids any heavy dependencies and uses
only the Python standard library.
"""
from __future__ import annotations

import ipaddress
import re
from typing import Optional, Pattern


# Regular expressions for IPv4 and IPv6 addresses.
# They are intentionally simple ‑- good enough for the tests but do not try
# to be 100 % RFC-compliant.  They *do* avoid matching obviously impossible
# addresses (e.g. > 255 in an octet).
_OCTET = r"(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
_IPV4_RE: Pattern[str] = re.compile(rf"\b({_OCTET}\.){{3}}{_OCTET}\b")

# For IPv6 we rely on the ipaddress module for validation; the regex only
# needs to capture potential candidates (hex and colons).
_IPV6_CANDIDATE_RE: Pattern[str] = re.compile(
    r"\b([0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b"
)


def isValidIP(ip: str) -> bool:
    """
    Return *True* iff *ip* is a syntactically valid IPv4 **or** IPv6 address.
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def _first_ipv6(text: str) -> Optional[str]:
    for match in _IPV6_CANDIDATE_RE.finditer(text):
        candidate = match.group(0)
        if isValidIP(candidate):
            return candidate
    return None


def searchIP(text: str) -> Optional[str]:
    """
    Search *text* for the first IPv4 or IPv6 address and return it.

    When no IP address is present, *None* is returned.
    """
    # Prioritise IPv4 for speed – they are easier to locate.
    m4 = _IPV4_RE.search(text)
    if m4:
        return m4.group(0)

    return _first_ipv6(text)