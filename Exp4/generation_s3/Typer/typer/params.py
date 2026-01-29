from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Tuple


_MISSING = object()


@dataclass
class OptionInfo:
    default: Any = _MISSING
    param_decls: Tuple[str, ...] = field(default_factory=tuple)
    help: str | None = None
    required: bool = False
    type: Any = None

    def __post_init__(self) -> None:
        # Required if default is missing or Ellipsis
        self.required = self.default is _MISSING or self.default is ...


@dataclass
class ArgumentInfo:
    default: Any = _MISSING
    param_decls: Tuple[str, ...] = field(default_factory=tuple)
    help: str | None = None
    required: bool = False
    type: Any = None

    def __post_init__(self) -> None:
        self.required = self.default is _MISSING or self.default is ...


def Option(default: Any = _MISSING, *param_decls: str, help: str | None = None, **kwargs) -> OptionInfo:
    # kwargs accepted for API-compat; ignored in this minimal implementation
    return OptionInfo(default=default, param_decls=tuple(param_decls), help=help)


def Argument(default: Any = _MISSING, *param_decls: str, help: str | None = None, **kwargs) -> ArgumentInfo:
    return ArgumentInfo(default=default, param_decls=tuple(param_decls), help=help)