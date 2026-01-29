"""
Celery - Distributed Task Queue
"""

__version__ = '5.3.0'
__author__ = 'Ask Solem'

from celery.app import Celery
from celery.result import AsyncResult

__all__ = ['Celery', 'AsyncResult', '__version__']