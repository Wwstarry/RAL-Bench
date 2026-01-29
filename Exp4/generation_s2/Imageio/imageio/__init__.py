"""
Minimal, pure-Python subset of the ImageIO API required by the tests.

This package provides a small portion of the ImageIO v3 interface:
- imageio.v3.imread
- imageio.v3.imwrite
- imageio.v3.imiter
- imageio.v3.improps
- imageio.v3.immeta
"""

from . import v3  # re-export module

__all__ = ["v3"]
__version__ = "0.0.test"