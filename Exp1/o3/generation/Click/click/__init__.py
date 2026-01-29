"""
Mini subset of the Click public interface.

Only the pieces required by the execution environment are implemented.
The real Click project is far more feature–rich – this is *not* a drop-in
replacement for every possible use-case.  It is, however, compatible with
the core surface that the kata-style tests exercise.
"""
from __future__ import annotations

from types import ModuleType
import sys

from .core import (
    Context,
    Command,
    Group,
    Option,
    Argument,
    echo,
    secho,
)
from .decorators import command, group, option, argument
from .testing import CliRunner

# Re-export the most common public names ---------------------------------------------------------
__all__ = [
    # decorators
    "command",
    "group",
    "option",
    "argument",
    # helpers
    "echo",
    "secho",
    # core objects
    "Context",
    "Command",
    "Group",
    # testing
    "CliRunner",
]

# Expose them under `click.*`
command.__name__ = "command"  # type: ignore[attr-defined]
group.__name__ = "group"  # type: ignore[attr-defined]

# Provide sub-modules so `import click.testing` continues to work --------------------------------
current_module = sys.modules[__name__]

def _create_stub(name: str) -> ModuleType:
    mod = ModuleType(f"{__name__}.{name}")
    setattr(current_module, name, mod)
    sys.modules[mod.__name__] = mod
    return mod


# click.core
sys.modules["click.core"] = sys.modules[__name__ + ".core"]

# click.decorators
sys.modules["click.decorators"] = sys.modules[__name__ + ".decorators"]

# click.testing
sys.modules["click.testing"] = sys.modules[__name__ + ".testing"]

# Provide empty stubs for utils and termui if they are imported by user code
for _sub in ("utils", "termui"):
    _create_stub(_sub)