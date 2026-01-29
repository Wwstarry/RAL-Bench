"""
Pure-Python steganography library implementing a subset of the public API of
the reference "Stegano" project.

This package exposes the following submodules:
- stegano.lsb
- stegano.red
- stegano.exifHeader
- stegano.wav
"""
from __future__ import annotations

from . import lsb, red, exifHeader, wav  # re-export for "from stegano import ..."

__all__ = ["lsb", "red", "exifHeader", "wav"]