"""
A small subset of the Astral API implemented in pure Python.

This package provides:
- LocationInfo
- astral.sun: sun(), sunrise(), sunset(), dawn(), dusk(), noon()
- astral.moon: phase()
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import tzinfo as _tzinfo
from typing import Optional, Union

from .location import LocationInfo

__all__ = ["LocationInfo"]

# Convenience re-exports (Astral exposes submodules; tests typically import from astral.sun / astral.moon)