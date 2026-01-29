"""
A tiny, pure-Python subset of the ImageIO v3 API used by the tests.

This repository intentionally implements only the minimal surface:
- imageio.v3.{imread, imwrite, imiter, improps, immeta}

The implementation is self-contained and does not depend on Pillow or other
third-party image libraries; it uses a small custom PNG codec for lossless
roundtrips and a simple custom animated container format for multi-frame data.
"""

from __future__ import annotations

from . import v3  # re-export module

__all__ = ["v3"]