"""
Minimal, safe-to-evaluate subset of Fail2Ban.

This package provides a small offline implementation of select API surfaces:
- fail2ban.server.jail.Jail
- fail2ban.server.filter helpers (isValidIP, searchIP) and Filter class

It is explicitly non-daemon, does not modify firewall rules, and operates
only on in-memory data and offline log parsing.
"""
__all__ = ["server"]
__version__ = "0.1.0-minimal"