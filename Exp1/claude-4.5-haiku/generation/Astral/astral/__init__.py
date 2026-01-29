"""
Astral: A pure Python sun and moon time calculation library.
"""

from .location import LocationInfo
from .sun import sun, sunrise, sunset
from .moon import phase

__all__ = [
    'LocationInfo',
    'sun',
    'sunrise',
    'sunset',
    'phase',
]

__version__ = '1.0.0'