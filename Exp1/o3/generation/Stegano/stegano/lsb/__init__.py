"""
Least-Significant-Bit steganography backend.
Hides information by replacing the LSB of every colour component.
"""
from .lsb import hide, reveal  # noqa: F401 – re-export for public API