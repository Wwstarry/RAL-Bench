"""
A lightweight, pure-Python subset of Loguru.

This module exposes a global ``logger`` object compatible with the core API of
the reference Loguru project for common use-cases and black-box tests.
"""

from ._logger import Logger

logger = Logger()

__all__ = ["logger", "Logger"]