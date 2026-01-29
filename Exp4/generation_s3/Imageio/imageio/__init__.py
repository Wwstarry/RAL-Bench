"""
A tiny, pure-Python (from the repository perspective) subset of ImageIO.

This package implements the small portion of the ImageIO v3 API required by the
test suite for this kata. It is not intended to be feature-complete.

Public entrypoints:
- imageio.v3.imread
- imageio.v3.imwrite
- imageio.v3.imiter
- imageio.v3.improps
- imageio.v3.immeta
"""

from __future__ import annotations

from . import v3 as v3

__all__ = ["v3"]