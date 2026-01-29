"""
Global data container
"""

from lib.core.datatype import AttribDict
from lib.core.log import LOGGER


# Command line options
cmdLineOptions = AttribDict()

# Configuration
conf = AttribDict()

# Knowledge base
kb = AttribDict()

# Logger instance
logger = LOGGER