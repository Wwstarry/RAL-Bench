import inspect
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class OptionInfo:
    default: Any = ...
    param_decls: Optional[tuple] = None
    help: Optional[str] = None
    show_default: bool = True
    prompt: Any = False
    confirmation_prompt: bool = False
    hide_input: bool = False
    is_flag: Optional[bool] = None
    flag_value: Any = None
    count: bool = False
    type: Any = None
    multiple: bool = False
    required: bool = False
    metavar: Optional[str] = None
    envvar: Optional[str] = None
    autocompletion: Optional[Callable] = None  # placeholder
    callback: Optional[Callable] = None


@dataclass
class ArgumentInfo:
    default: Any = ...
    help: Optional[str] = None
    type: Any = None
    required: bool = False
    metavar: Optional[str] = None
    envvar: Optional[str] = None
    autocompletion: Optional[Callable] = None  # placeholder
    callback: Optional[Callable] = None


def Option(
    default: Any = ...,
    *param_decls: str,
    help: Optional[str] = None,
    show_default: bool = True,
    prompt: Any = False,
    confirmation_prompt: bool = False,
    hide_input: bool = False,
    is_flag: Optional[bool] = None,
    flag_value: Any = None,
    count: bool = False,
    type: Any = None,
    multiple: bool = False,
    required: bool = False,
    metavar: Optional[str] = None,
    envvar: Optional[str] = None,
    autocompletion: Optional[Callable] = None,
    callback: Optional[Callable] = None,
):
    """
    Declare a command option for a function parameter.

    Returns an OptionInfo marker that Typer uses to build a Click option.
    """
    decls = tuple(param_decls) if param_decls else None
    return OptionInfo(
        default=default,
        param_decls=decls,
        help=help,
        show_default=show_default,
        prompt=prompt,
        confirmation_prompt=confirmation_prompt,
        hide_input=hide_input,
        is_flag=is_flag,
        flag_value=flag_value,
        count=count,
        type=type,
        multiple=multiple,
        required=required,
        metavar=metavar,
        envvar=envvar,
        autocompletion=autocompletion,
        callback=callback,
    )


def Argument(
    default: Any = ...,
    *,
    help: Optional[str] = None,
    type: Any = None,
    required: bool = False,
    metavar: Optional[str] = None,
    envvar: Optional[str] = None,
    autocompletion: Optional[Callable] = None,
    callback: Optional[Callable] = None,
):
    """
    Declare a command argument for a function parameter.

    Returns an ArgumentInfo marker that Typer uses to build a Click argument.
    """
    return ArgumentInfo(
        default=default,
        help=help,
        type=type,
        required=required,
        metavar=metavar,
        envvar=envvar,
        autocompletion=autocompletion,
        callback=callback,
    )


def is_option_marker(value: Any) -> bool:
    return isinstance(value, OptionInfo)


def is_argument_marker(value: Any) -> bool:
    return isinstance(value, ArgumentInfo)


def get_param_default(param: inspect.Parameter) -> Any:
    if param.default is inspect._empty:
        return ...
    return param.default