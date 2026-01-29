from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class OptionInfo:
    default: Any = ...
    param_decls: tuple[str, ...] = ()
    help: str | None = None
    show_default: bool = True
    is_flag: bool | None = None
    hidden: bool = False

    # accept many Typer kwargs for compatibility
    prompt: Any = None
    envvar: Any = None
    callback: Any = None
    case_sensitive: bool = True
    count: bool = False


@dataclass(frozen=True)
class ArgumentInfo:
    default: Any = ...
    help: str | None = None
    metavar: str | None = None
    nargs: Any = None
    envvar: Any = None
    callback: Any = None


def Option(default: Any = ..., *param_decls: str, **kwargs: Any) -> OptionInfo:
    return OptionInfo(
        default=default,
        param_decls=tuple(param_decls),
        help=kwargs.get("help"),
        show_default=kwargs.get("show_default", True),
        is_flag=kwargs.get("is_flag"),
        hidden=kwargs.get("hidden", False),
        prompt=kwargs.get("prompt"),
        envvar=kwargs.get("envvar"),
        callback=kwargs.get("callback"),
        case_sensitive=kwargs.get("case_sensitive", True),
        count=kwargs.get("count", False),
    )


def Argument(default: Any = ..., **kwargs: Any) -> ArgumentInfo:
    return ArgumentInfo(
        default=default,
        help=kwargs.get("help"),
        metavar=kwargs.get("metavar"),
        nargs=kwargs.get("nargs"),
        envvar=kwargs.get("envvar"),
        callback=kwargs.get("callback"),
    )