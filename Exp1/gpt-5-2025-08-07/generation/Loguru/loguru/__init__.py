# Minimal pure-Python Loguru-compatible facade

from ._logger import Logger as _Logger

# Create a singleton logger, similar to Loguru's design
logger = _Logger()

# Expose internal stub for compatibility
# Users/tests may import loguru._logger
from . import _logger as _logger