"""
A tiny, pure-Python subset of the Loguru API.

This repository is intended to be compatible with a small, commonly used part
of Loguru's public surface as exercised by the test suite.
"""

from ._logger import logger  # noqa: F401
from . import _logger as _logger  # re-export module for tests importing loguru._logger

__all__ = ["logger"]