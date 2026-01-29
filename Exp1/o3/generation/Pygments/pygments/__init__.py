"""
A very small, pure-python subset of the original pygments project
sufficient for the needs of the test-suite shipped with this task.

Only a handful of languages, formatters and styles are implemented.
The public API that most user-code relies on is, however, kept intact.
"""

from importlib import import_module
from types import ModuleType

# Public helpers -------------------------------------------------------------

from pygments.lex import lex   # type: ignore  # re-export
from pygments.highlight import highlight  # type: ignore  # re-export

# Expose the two formatters via a pseudo ‘pygments.formatters’ module
# so that “from pygments.formatters import HtmlFormatter” keeps working,
# even though the actual code lives in pygments/formatters/html.py
import sys as _sys
_formatters_pkg = import_module("pygments.formatters")
_sys.modules["pygments.formatters"] = _formatters_pkg

# Ditto for lexers, styles, filters
_sys.modules["pygments.lexers"] = import_module("pygments.lexers")
_sys.modules["pygments.styles"] = import_module("pygments.styles")
_sys.modules["pygments.filters"] = import_module("pygments.filters")

# Convenience re-exports
from pygments.token import Token  # noqa: E402 pylint: disable=ungrouped-imports
from pygments.util import ClassNotFound  # noqa: E402 pylint: disable=ungrouped-imports

__all__ = [
    "lex",
    "highlight",
    "Token",
    "ClassNotFound",
]