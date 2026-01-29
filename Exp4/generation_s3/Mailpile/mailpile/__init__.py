"""
A small, self-contained subset of Mailpile core utilities.

This repository intentionally includes only a few modules required by tests:
- safe_popen: safe subprocess helpers
- util: general utilities (text cleaning, base36, cache, filesystem helpers)
- vcard: basic vCard line parsing/serialization
- i18n: gettext passthrough helpers
"""

from .i18n import gettext as _  # Common Mailpile convention

__all__ = ['_']