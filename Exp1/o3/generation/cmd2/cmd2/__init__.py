"""
A **very** small subset of the public surface of the ``cmd2`` project
implemented in pure Python.  Only the behaviour needed by the test-suite
that accompanies this repository is provided.  It is **not** a complete
or fully-featured replacement for the real ``cmd2`` package.

The primary goals are:

* Keep the same import locations used by the reference project
  (``Cmd``, ``Cmd2``, ``Statement``, …).
* Provide utilities for output capture and transcript testing which the
  black-box tests rely on.
* Offer extremely light-weight argument‐parsing helpers so that tests
  can introspect command lines in a reasonably convenient fashion.
"""
from importlib import import_module
from types import ModuleType

# The public sub-modules we expose.  They are created on demand so that
# ``import cmd2.parsing`` still works even if users only imported
# ``cmd2``.
_submodules = {
    'cmd2': '.cmd2',
    'parsing': '.parsing',
    'utils': '.utils',
}

def __getattr__(name: str) -> ModuleType:
    # Handle lazy-loading of sub-packages
    if name in _submodules:  # pragma: no cover
        module = import_module(__name__ + _submodules[name])
        globals()[name] = module
        return module
    raise AttributeError(name)


# Re-export the key runtime symbols that black-box tests expect.
from .cmd2 import Cmd2, Cmd, Statement, run_transcript               # noqa:  E402  (import after package global)
from .utils import capture_output                                    # noqa:  E402

__all__ = [
    # Core class
    'Cmd2',
    'Cmd',

    # Parsing helper
    'Statement',

    # Utilities
    'capture_output',
    'run_transcript',
]

__version__ = '0.1.0'