# This file will almost never be reached because we inject the sub-module
# dynamically from ``typer.__init__``.  It exists solely to satisfy tools that
# expect a concrete file on disk.
from click.testing import CliRunner

__all__ = ["CliRunner"]