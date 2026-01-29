"""
Pure-Python subset of the Astral API used by the tests.

This is not a full Astral reimplementation; it provides the core public API:
- LocationInfo and Observer
- astral.sun: sun(), sunrise(), sunset(), noon(), dawn(), dusk
- astral.moon: phase()

No third-party dependencies are used.
"""

from __future__ import annotations

from .location import LocationInfo, Observer

__all__ = ["LocationInfo", "Observer"]

# Re-export submodules for API-compatibility
from . import sun, moon  # noqa: E402,F401