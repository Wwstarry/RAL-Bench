"""
dataset is a pure Python lightweight tabular data access layer that is
API-compatible with the core parts of the reference Dataset project.
"""
from .database import connect

__all__ = ['connect']
__version__ = '1.0.0'