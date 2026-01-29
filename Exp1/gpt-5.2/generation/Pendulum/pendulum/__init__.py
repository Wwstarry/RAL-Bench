"""
A small, pure-Python subset of the Pendulum API.

This package is intended to be API-compatible with the core parts of Pendulum
used in common black-box tests:
- pendulum.datetime(..., tz=...)
- pendulum.parse(...)
- pendulum.timezone(...)
- DateTime.in_timezone(...)
- DateTime.add(...)
- DateTime subtraction producing Duration
- pendulum.duration(...)
- DateTime.diff_for_humans(...)
"""

from __future__ import annotations

from .datetime import DateTime, datetime, now, parse
from .timezone import Timezone, timezone, local_timezone, UTC
from .duration import Duration, duration

__all__ = [
    "DateTime",
    "Duration",
    "Timezone",
    "UTC",
    "datetime",
    "now",
    "parse",
    "timezone",
    "local_timezone",
    "duration",
]