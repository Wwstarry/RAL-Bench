"""
dataset - a pure Python lightweight tabular data access layer
"""
from .database import connect

__all__ = ['connect']
__version__ = '1.6.2' # Mimic reference version for compatibility