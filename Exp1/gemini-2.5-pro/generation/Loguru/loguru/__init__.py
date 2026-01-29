from . import _logger
from ._logger import Logger

# The main logger instance, configured to be used globally.
# It is created here without any sinks. Tests or applications
# are expected to configure it with logger.add().
logger = Logger()