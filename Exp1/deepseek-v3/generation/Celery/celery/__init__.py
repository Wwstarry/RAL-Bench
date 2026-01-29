"""Celery - Distributed Task Queue"""

from .app import Celery

__version__ = '5.3.0'
__author__ = 'Ask Solem'
__contact__ = 'auvipy@gmail.com'
__homepage__ = 'https://celeryproject.org/'
__docformat__ = 'restructuredtext'

# -eof meta-

# Import commonly used items
from .app import Celery as _Celery

# Lazy loading
def __getattr__(name):
    if name == 'Celery':
        return _Celery
    raise AttributeError(f"module 'celery' has no attribute '{name}'")

# Legacy imports for compatibility
VERSION = __version__