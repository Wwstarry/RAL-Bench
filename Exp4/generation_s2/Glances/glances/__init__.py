"""
Minimal, API-compatible subset of the Glances project for one-shot CSV output.

This package provides a CLI via `python -m glances` supporting:
- --help
- -V / --version
- --stdout-csv <FIELDS>
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"