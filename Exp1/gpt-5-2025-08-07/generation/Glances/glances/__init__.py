"""
Minimal glances-compatible package for cross-platform system metrics and CLI.

This package provides:
- Version information via glances.__version__
- A CLI entrypoint runnable with: python -m glances
- One-shot CSV output for selected fields via --stdout-csv
"""

__all__ = ["__version__"]

# Version string shown by the CLI (-V/--version)
__version__ = "0.1.0"