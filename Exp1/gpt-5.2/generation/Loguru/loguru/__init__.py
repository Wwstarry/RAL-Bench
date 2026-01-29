"""
A small, pure-Python subset of Loguru.

This repository re-implements a core-compatible API used by tests:
- loguru.logger singleton
- logger.add/remove
- logger.debug/info/warning/error/exception/log
- logger.bind/opt
- sinks: callable and file path
- basic formatting with time, level, message, extra, exception
"""

from ._logger import logger  # noqa: F401

__all__ = ["logger"]