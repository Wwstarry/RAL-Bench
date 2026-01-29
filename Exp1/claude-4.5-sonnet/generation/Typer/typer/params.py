"""Parameter definitions for Typer."""

from typing import Any, Optional, List


class ParamInfo:
    """Base class for parameter information."""
    
    def __init__(
        self,
        default: Any = None,
        *,
        param_decls: Optional[List[str]] = None,
        is_argument: bool = False,
        **kwargs: Any
    ):
        self.default = default
        self.param_decls = param_decls or []
        self.is_argument = is_argument
        self.kwargs = kwargs


def Option(
    default: Any = None,
    *param_decls: str,
    help: Optional[str] = None,
    **kwargs: Any
) -> Any:
    """Define a CLI option."""
    return ParamInfo(
        default=default,
        param_decls=list(param_decls),
        is_argument=False,
        help=help,
        **kwargs
    )


def Argument(
    default: Any = None,
    *param_decls: str,
    help: Optional[str] = None,
    **kwargs: Any
) -> Any:
    """Define a CLI argument."""
    return ParamInfo(
        default=default,
        param_decls=list(param_decls),
        is_argument=True,
        help=help,
        **kwargs
    )