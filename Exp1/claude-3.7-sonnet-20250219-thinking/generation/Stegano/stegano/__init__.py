"""
Stegano - Pure Python Steganography Library

This library provides several steganographic methods to hide or reveal data:
- LSB (Least Significant Bit)
- Red channel modification
- EXIF header manipulation
- WAV audio
"""
from stegano import lsb
from stegano import red
from stegano import exifHeader
from stegano import wav

__version__ = "0.11.0"  # Version number consistent with a mature library