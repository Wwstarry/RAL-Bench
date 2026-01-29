"""
Loguru - A pure Python logging library compatible with the reference Loguru project.
"""

from loguru._logger import Logger

# Create a singleton logger instance
logger = Logger()

__all__ = ["logger"]