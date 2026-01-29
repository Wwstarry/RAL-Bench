import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple, get_args, get_origin

import click

from .exceptions import Exit
from .params import (
    ArgumentInfo,
    OptionInfo,
    get_param_default,
    is_argument_marker,
    is_option_marker,
)


def _annotation_to_click_type(annotation: Any):
    if annotation is None or annotation is inspect._empty:
        return None
    origin = get_origin(annotation)
    if origin is Optional:
        args = [a for a in get_args(annotation) if a is not type(None)]  # noqa: E721
        annotation = args[0] if args else str
    elif origin is list or origin is List:
        # click handles multiple via OptionInfo.multiple rather than list type
        args = get_args(annotation)
        annotation = args[0] if args else str

    mapping = {
        str: click.STRING,
        int: click.INT,
        float: click.FLOAT,
        bool: click.BOOL,
    }
    return mapping.get(annotation, None)


def _build_option_param(
    name: str, annotation: Any, info: OptionInfo
) -> click.Option:
    decls: Tuple[str, ...]
    if info.param_decls:
        decls = info.param_decls
    else:
        # Default to "--param-name"
        decls = (f"--{name.replace('_', '-')}",)

    default = info.default
    if default is ...:
        default = None

    click_type = info.type if info.type is not None else _annotation_to_click_type(annotation)

    # Derive is_flag if not set and annotated bool or default is bool
    is_flag = info.is_flag
    if is_flag is None:
        if annotation is bool or isinstance(default, bool):
            is_flag = True
        else:
            is_flag = False

    param = click.Option(
        param_decls=list(decls),
        help=info.help,
        show_default=info.show_default,
        prompt=info.prompt,
        confirmation_prompt=info.confirmation_prompt,
        hide_input=info.hide_input,
        is_flag=is_flag,
        flag_value=info.flag_value,
        count=info.count,
        type=click_type,
        multiple=info.multiple,
        required=info.required,
        default=default if not info.required else (None if default is None else default),
        metavar=info.metavar,
        envvar=info.envvar,
        callback=info.callback,
        expose_value=True,
        name=name,
    )
    return param


def _build_argument_param(
    name: str, annotation: Any, info: ArgumentInfo
) -> click.Argument:
    default = info.default
    if default is ...:
        default = None

    click_type = info.type if info.type is not None else _annotation_to_click_type(annotation)

    required = info.required
    if info.default is ... and not required:
        # If no default was provided, assume required for positional arguments.
        required = True

    param = click.Argument(
        param_decls=[name],
        type=click_type,
        required=required,
        default=default if not required else None,
        metavar=info.metavar,
        envvar=info.envvar,
        callback=info.callback,
        expose_value=True,
    )
    return param


def _analyze_function_params(func: Callable) -> List[click.Parameter]:
    sig = inspect.signature(func)
    params: List[click.Parameter] = []

    for p in sig.parameters.values():
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            raise TypeError("Variadic parameters (*args/**kwargs) are not supported in this mini Typer")

        annotation = p.annotation
        default = get_param_default(p)

        if is_option_marker(default):
            info: OptionInfo = default
            params.append(_build_option_param(p.name, annotation, info))
        elif is_argument_marker(default):
            info2: ArgumentInfo = default
            params.append(_build_argument_param(p.name, annotation, info2))
        else:
            # Heuristic: positional argument unless it has a default -> option.
            if default is ...:
                params.append(_build_argument_param(p.name, annotation, ArgumentInfo(default=..., required=True)))
            else:
                params.append(_build_option_param(p.name, annotation, OptionInfo(default=default)))

    # Click expects arguments before options in params list.
    args = [p for p in params if isinstance(p, click.Argument)]
    opts = [p for p in params if isinstance(p, click.Option)]
    return args + opts


def _wrap_callback(func: Callable) -> Callable:
    def callback(**kwargs):
        try:
            result = func(**kwargs)
        except Exit as e:
            raise click.exceptions.Exit(code=getattr(e, "exit_code", int(e.code) if e.code is not None else 0))
        except SystemExit as e:
            code = e.code if e.code is not None else 0
            raise click.exceptions.Exit(code=int(code))
        # If a command returns an int, interpret as exit code (common in CLIs).
        if isinstance(result, int) and result != 0:
            raise click.exceptions.Exit(code=int(result))
        return result

    return callback


class Typer:
    """
    Create a CLI application.

    Supports:
    - @app.command() to register commands
    - invoking via Click (app() / app.main / CliRunner.invoke)
    """

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        help: Optional[str] = None,
        add_completion: bool = False,
        no_args_is_help: bool = False,
        invoke_without_command: bool = False,
    ):
        self.name = name
        self.help = help
        self.add_completion = add_completion
        self.no_args_is_help = no_args_is_help
        self.invoke_without_command = invoke_without_command

        self._commands: Dict[str, click.Command] = {}
        self._group: Optional[click.Group] = None

    def command(self, name: Optional[str] = None, *, help: Optional[str] = None):
        def decorator(func: Callable):
            cmd_name = name or func.__name__.replace("_", "-")
            params = _analyze_function_params(func)
            cmd = click.Command(
                name=cmd_name,
                params=params,
                callback=_wrap_callback(func),
                help=help or (func.__doc__.strip() if func.__doc__ else None),
            )
            self._commands[cmd_name] = cmd
            # Invalidate cached group so it rebuilds with new commands
            self._group = None
            return func

        return decorator

    def add_typer(self, other: "Typer", *, name: Optional[str] = None, help: Optional[str] = None):
        grp = other._get_group()
        grp.name = name or grp.name
        if help is not None:
            grp.help = help
        self._commands[grp.name] = grp
        self._group = None
        return grp

    def _get_group(self) -> click.Group:
        if self._group is not None:
            return self._group

        group_name = self.name
        grp = click.Group(
            name=group_name,
            help=self.help,
            commands=self._commands.copy(),
            invoke_without_command=self.invoke_without_command,
            no_args_is_help=self.no_args_is_help,
        )
        self._group = grp
        return grp

    # Click-compatible entry points
    def __call__(self, *args, **kwargs):
        return self._get_group()(*args, **kwargs)

    def main(self, *args, **kwargs):
        return self._get_group().main(*args, **kwargs)

    @property
    def registered_commands(self):
        return list(self._commands.keys())