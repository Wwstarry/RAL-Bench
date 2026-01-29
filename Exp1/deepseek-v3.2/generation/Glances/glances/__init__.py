"""
Glances - A cross-platform system monitoring tool
"""

__version__ = "3.5.0"
__author__ = "Glances Team"
__license__ = "LGPL"

from glances.core import Glances
from glances.cli import main

__all__ = ['Glances', 'main']