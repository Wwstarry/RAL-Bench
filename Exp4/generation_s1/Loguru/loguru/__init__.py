from ._logger import Logger

__version__ = "0.0.0"

# Singleton, like Loguru
logger = Logger()

__all__ = ["logger", "Logger"]