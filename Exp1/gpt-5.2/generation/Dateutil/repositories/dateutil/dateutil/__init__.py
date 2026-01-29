"""
A lightweight, pure-Python subset of python-dateutil.

This package implements a compatible public surface for:
- dateutil.parser.parse
- dateutil.relativedelta.relativedelta
- dateutil.rrule.rrule (+ constants/weekday helpers)
- dateutil.tz (UTC/gettz)

It is intended to satisfy the black-box tests shipped with this kata.
"""

from . import parser, relativedelta, rrule, tz

__all__ = ["parser", "relativedelta", "rrule", "tz"]