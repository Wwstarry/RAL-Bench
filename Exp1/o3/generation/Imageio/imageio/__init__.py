"""
Minimal stub of the ``imageio`` package that exposes the subset of the v3 API
required by the test-suite.
"""

from __future__ import annotations

# Re-export the v3 sub-module at package import time so that users/tests can do
# ``import imageio, imageio.v3`` or ``from imageio import v3``.
from . import v3 as v3  # noqa: F401

# What we make public at the top-level.  Arranged to be similar to the real
# ImageIO package, but we only expose what the tests need.
__all__ = ["v3"]