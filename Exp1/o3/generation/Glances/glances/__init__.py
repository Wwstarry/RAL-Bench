"""
A very small, self-contained subset of the Glances package
exposing only what is strictly required by the test-suite.

It purposefully supports just enough functionality to satisfy:
  * `python -m glances --help`
  * `python -m glances -V / --version`
  * `python -m glances --stdout-csv ...`

Nothing more, nothing less.
"""

from __future__ import annotations

__all__ = [
    "__version__",
]

# Keep the version in a single place so both the package and CLI share it.
__version__: str = "0.0.0.dev0"