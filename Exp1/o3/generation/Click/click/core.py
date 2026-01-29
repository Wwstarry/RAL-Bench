"""
A **very** small re-implementation of the bits of ``click.core`` required by the
test-suite shipped with this kata.

It purposefully ignores the vast majority of edge-cases covered by the
up-stream project.  If you need those additional capabilities – just install
real Click instead :-)
"""
from __future__ import annotations

import sys
import os
import io
import contextlib
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Sequence,
    Tuple,
    Optional,
    Union,
    Iterable,
)

Color = Optional[str]
Callback = Callable[..., Any]


def echo(message: str = "", file=None, nl: bool = True, err: bool = False) -> None:
    """
    Simple echo helper that mirrors :func:`click.echo`.

    Arguments:
        message: text to write.
        file: override file object.  If omitted, ``stdout``/``stderr`` is selected
              based on *err*.
        nl: add a trailing newline.
        err: if *True* write to :pydata:`sys.stderr` instead of :pydata:`sys.stdout`.
    """
    f = file if file is not None else (sys.stderr if err else sys.stdout)
    if message:
        f.write(str(message))
    if nl:
        f.write("\n")
    f.flush()


def secho(
    message: str = "",
    file=None,
    nl: bool = True,
    err: bool = False,
    fg: Color = None,
    bg: Color = None,
    bold: bool = False,
    underline: bool = False,
    color: bool = True,
) -> None:
    """
    Very small subset of :func:`click.secho` that only supports a handful of
    style options.  We rely on ANSI sequences.

    The *color* toggle unconditionally enables / disables colour output.  This
    differs from real Click which consults auto-detection heuristics – for this
    pared-down implementation the tests control it explicitly.
    """
    styles: List[str] = []
    if color:
        if fg:
            fg_codes = {
                "black": 30,
                "red": 31,
                "green": 32,
                "yellow": 33,
                "blue": 34,
                "magenta": 35,
                "cyan": 36,
                "white": 37,
            }
            styles.append(str(fg_codes.get(fg, 37)))
        if bg:
            bg_codes = {
                "black": 40,
                "red": 41,
                "green": 42,
                "yellow": 43,
                "blue": 44,
                "magenta": 45,
                "cyan": 46,
                "white": 47,
            }
            styles.append(str(bg_codes.get(bg, 40)))
        if bold:
            styles.append("1")
        if underline:
            styles.append("4")

    start = f"\033[{';'.join(styles)}m" if styles else ""
    end = "\033[0m" if styles else ""
    echo(f"{start}{message}{end}", file=file, nl=nl, err=err)


# ------------------------------------------------------------------------------
# Parameter types & parsing helpers
# ------------------------------------------------------------------------------

class BadParameter(Exception):
    pass


class MissingParameter(Exception):
    pass


class NoSuchOption(Exception):
    pass


class UsageError(Exception):
    def __init__(self, message: str, ctx: Optional["Context"] = None) -> None:
        super().__init__(message)
        self.ctx = ctx
        self.message = message

    def __str__(self) -> str:  # pragma: no cover
        return self.message


class Parameter:
    param_type_name = "parameter"

    def __init__(
        self,
        name: str,
        param_type: str = "argument",
        required: bool = False,
        default: Any = None,
        multiple: bool = False,
        type: Callable[[str], Any] = str,
        help: Optional[str] = None,
        prompt: Union[bool, str] = False,
    ) -> None:
        self.name = name
        self.param_type = param_type
        self.required = required
        self.default = default
        self.multiple = multiple
        self.type = type
        self.help = help
        self.prompt = prompt

    def consume_value(self, value: Optional[str]) -> Any:
        """
        Convert *value* using ``self.type``.  Handles missing / default /
        required logic.
        """
        if value is None:
            if self.prompt:
                prompt_text = self.prompt if isinstance(self.prompt, str) else f"{self.name}: "
                echo(prompt_text, nl=False)
                value = input()
            elif self.default is not None:
                value = self.default
            elif self.required:
                raise MissingParameter(f"Missing {self.param_type} '{self.name}'.")
        try:
            if self.multiple and isinstance(value, list):
                return [self.type(v) for v in value]
            return self.type(value)
        except Exception as exc:  # pragma: no cover
            raise BadParameter(str(exc)) from exc

    def make_usage(self) -> str:
        raise NotImplementedError()


class Argument(Parameter):
    param_type_name = "argument"

    def __init__(self, name: str, **attrs: Any) -> None:
        super().__init__(name, param_type="argument", **attrs)

    def make_usage(self) -> str:
        t = f"<{self.name}>"
        if not self.required:
            t = f"[{t}]"
        if self.multiple:
            t = f"{t}..."
        return t


class Option(Parameter):
    param_type_name = "option"

    def __init__(
        self,
        param_decls: Sequence[str],
        is_flag: bool = False,
        **attrs: Any,
    ) -> None:
        if not param_decls:
            raise TypeError("At least one option string is required.")
        self.param_decls = list(param_decls)
        name = self._infer_name()
        super().__init__(name, param_type="option", **attrs)
        self.is_flag = is_flag

    def _infer_name(self) -> str:
        # Use the longest declaration without leading dashes
        decl = max(self.param_decls, key=len)
        return decl.lstrip("-").replace("-", "_")

    def matches(self, token: str) -> bool:
        return token in self.param_decls or token.split("=", 1)[0] in self.param_decls

    def consume(self, args: List[str]) -> Tuple[Optional[str], List[str]]:
        """
        Consume this option from *args*.

        Returns a tuple of (value, remaining_args).  If the option is not found,
        returns (None, args).
        """
        if not args:
            return None, args

        tok = args[0]
        if not self.matches(tok):
            return None, args

        # It's our option, pop it
        args.pop(0)

        if self.is_flag:
            return True, args

        if "=" in tok:
            _, val = tok.split("=", 1)
            return val, args

        if not args:
            raise MissingParameter(f"Option '{tok}' requires an argument.")

        return args.pop(0), args

    def make_usage(self) -> str:
        # Show first declaration
        first = self.param_decls[0]
        if self.is_flag:
            usage = f"[{first}]"
        else:
            usage = f"[{first} <{self.name}>]"
        return usage


# ------------------------------------------------------------------------------
# Command, Group, Context
# ------------------------------------------------------------------------------

class Context:
    """
    Extremely simplified version of :class:`click.Context`.
    """

    def __init__(
        self,
        command: "Command",
        parent: Optional["Context"] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.command = command
        self.parent = parent
        self.params: Dict[str, Any] = params or {}
        self.obj: Any = None

    def exit(self, code: int = 0) -> None:
        sys.exit(code)

    def fail(self, message: str) -> None:
        raise UsageError(message, self)


class Command:
    """
    A callable shell command.
    """

    def __init__(
        self,
        name: str,
        callback: Optional[Callback],
        params: Optional[List[Parameter]] = None,
        help: Optional[str] = None,
    ) -> None:
        self.name = name
        self.callback = callback
        self.params: List[Parameter] = params or []
        self.help = help or (callback.__doc__.strip() if callback and callback.__doc__ else "")
        self.short_help = self.help.splitlines()[0] if self.help else ""

    # --------------------------------------------------------------------- Parsing

    def _parse_options(
        self, args: List[str]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Extract option parameters from *args*.  Returns (params, remaining_args).
        """
        params: Dict[str, Any] = {}
        remaining = list(args)

        # iterate until first non-option or no more args
        i = 0
        while i < len(remaining):
            token = remaining[i]
            if token == "--":
                # explicit end of options marker
                remaining = remaining[i + 1 :]
                break

            # Option?
            matched_param: Optional[Option] = None
            for p in self.params:
                if isinstance(p, Option) and p.matches(token):
                    matched_param = p
                    break

            if matched_param is None:
                if token.startswith("-"):
                    raise NoSuchOption(f"No such option: {token}")
                break  # first non-option

            # consume its value(s)
            val, leftovers = matched_param.consume(remaining[i:])

            if matched_param.multiple:
                params.setdefault(matched_param.name, []).append(
                    matched_param.consume_value(val)
                )
            else:
                params[matched_param.name] = matched_param.consume_value(val)

            # adjust list
            consumed = len(remaining[i:]) - len(leftovers)
            for _ in range(consumed):
                remaining.pop(i)

        return params, remaining

    def _parse_args(self, args: List[str]) -> Dict[str, Any]:
        parsed: Dict[str, Any] = {}

        # 1. options
        opts, remaining = self._parse_options(args)
        parsed.update(opts)

        # 2. positional arguments
        arg_params = [p for p in self.params if isinstance(p, Argument)]
        for arg in arg_params:
            if not remaining:
                if arg.required and arg.default is None:
                    raise MissingParameter(f"Missing argument '{arg.name}'.")
                else:
                    parsed[arg.name] = arg.default
            else:
                if arg.multiple:
                    vals = remaining
                    remaining = []
                    parsed[arg.name] = arg.consume_value(vals)
                else:
                    parsed[arg.name] = arg.consume_value(remaining.pop(0))
        if remaining:
            raise UsageError(f"Got unexpected extra argument {' '.join(remaining)}")
        return parsed

    # --------------------------------------------------------------------- Invocation

    def make_context(
        self, info_name: Optional[str], args: List[str], parent: Optional[Context] = None
    ) -> Context:
        ctx = Context(self, parent)
        ctx.params = self._parse_args(list(args))
        return ctx

    def invoke(self, ctx: Context) -> Any:
        if self.callback is None:
            return None
        # Maintain call signature: extract parameters
        return self.callback(**ctx.params)

    def main(self, args: Optional[Sequence[str]] = None, prog_name: Optional[str] = None) -> None:
        """
        Entrypoint for command-line execution.
        """
        argv = list(sys.argv[1:] if args is None else args)
        try:
            if "--help" in argv or "-h" in argv:
                echo(self.get_help())
                sys.exit(0)
            ctx = self.make_context(prog_name or self.name, argv)
            rv = self.invoke(ctx)
            if isinstance(rv, int):
                sys.exit(rv)
        except UsageError as e:
            echo(f"Error: {e}", err=True)
            sys.exit(2)

    # --------------------------------------------------------------------- Help & usage

    def get_usage_pieces(self) -> List[str]:
        pieces = []
        for p in self.params:
            pieces.append(p.make_usage())
        return pieces

    def get_usage(self) -> str:
        joined = " ".join(self.get_usage_pieces())
        return f"Usage: {self.name} {joined}".rstrip()

    def format_options(self) -> str:
        out_lines = []
        for p in self.params:
            if isinstance(p, Option):
                flags = ", ".join(p.param_decls)
                default = f" [default: {p.default}]" if p.default is not None else ""
                help_text = p.help or ""
                out_lines.append(f"  {flags:20} {help_text}{default}")
        return "\n".join(out_lines)

    def format_arguments(self) -> str:
        out_lines = []
        for p in self.params:
            if isinstance(p, Argument):
                help_text = p.help or ""
                out_lines.append(f"  {p.name:20} {help_text}")
        return "\n".join(out_lines)

    def get_help(self) -> str:
        lines = [self.get_usage()]
        if self.help:
            lines.append("")
            lines.append(self.help)
        opts = self.format_options()
        if opts:
            lines.append("")
            lines.append("Options:")
            lines.append(opts)
        args_help = self.format_arguments()
        if args_help:
            lines.append("")
            lines.append("Arguments:")
            lines.append(args_help)
        return "\n".join(lines)

    # --------------------------------------------------------------------- Callable

    def __call__(self, *args: str, **kwargs: Any) -> None:  # pragma: no cover
        return self.main(list(args))


class Group(Command):
    """
    A command that dispatches to sub-commands.
    """

    def __init__(self, name: str, callback: Optional[Callback], **attrs: Any) -> None:
        super().__init__(name, callback, **attrs)
        self.commands: Dict[str, Command] = {}

    # ------------------------------------------------------------------ Registration

    def command(self, *param_decls: str, **attrs: Any):
        """
        Define a sub-command in decorator style.

        Example::

            @cli.command()
            def sub():
                ...
        """

        def decorator(f: Callback) -> Command:
            cmd = CommandBuilder.from_callback(f, param_decls, attrs)
            self.add_command(cmd)
            return cmd

        return decorator

    def group(self, *param_decls: str, **attrs: Any):
        """
        Define a nested sub-group in decorator style.
        """

        def decorator(f: Callback) -> "Group":
            grp = CommandBuilder.from_group_callback(f, param_decls, attrs)
            self.add_command(grp)
            return grp

        return decorator

    def add_command(self, cmd: Command, name: Optional[str] = None) -> None:
        self.commands[name or cmd.name] = cmd

    # ------------------------------------------------------------------ Overrides

    def _parse_args(self, args: List[str]) -> Dict[str, Any]:
        """
        Groups consume parameters until the first token that is a registered
        sub-command.  Remaining args are passed to that sub-command.
        """
        # Parse our own options/args
        params, remainder = self._parse_options(args)
        # Find subcommand
        if remainder:
            cmd_name = remainder.pop(0)
            cmd = self.commands.get(cmd_name)
            if not cmd:
                raise UsageError(f"No such command '{cmd_name}'.")
            # Create context for self (without callback) and delegate
            ctx = Context(self, parent=None, params=params)
            sub_ctx = cmd.make_context(cmd.name, remainder, parent=ctx)
            return {"_sub_ctx": sub_ctx, "_sub_cmd": cmd}
        else:
            return params

    def invoke(self, ctx: Context) -> Any:
        # Check if we have subcontext to run
        if "_sub_cmd" in ctx.params:
            sub_cmd: Command = ctx.params["_sub_cmd"]
            sub_ctx: Context = ctx.params["_sub_ctx"]
            return sub_cmd.invoke(sub_ctx)
        else:
            if self.callback:
                return self.callback(**{k: v for k, v in ctx.params.items() if not k.startswith("_")})
            # else show help
            echo(self.get_help())
            return None

    def get_usage(self) -> str:
        base = super().get_usage()
        if self.commands:
            base = f"{base} COMMAND [ARGS]..."
        return base

    def get_help(self) -> str:
        lines = [self.get_usage()]
        if self.help:
            lines.append("")
            lines.append(self.help)
        if self.commands:
            lines.append("")
            lines.append("Commands:")
            longest = max((len(c) for c in self.commands), default=0)
            for name, cmd in sorted(self.commands.items()):
                lines.append(f"  {name:{longest}}  {cmd.short_help}")
        opts = self.format_options()
        if opts:
            lines.append("")
            lines.append("Options:")
            lines.append(opts)
        return "\n".join(lines)


# ------------------------------------------------------------------------------
# Command builder from decorated function
# ------------------------------------------------------------------------------

class CommandBuilder:
    """
    Helper that collects parameter information stored on functions by the
    decorator layer and creates Command / Group objects.
    """

    @staticmethod
    def collect_params(f: Callback) -> List[Parameter]:
        return list(getattr(f, "__click_params__", []))

    @classmethod
    def from_callback(cls, f: Callback, param_decls: Sequence[str], attrs: Dict[str, Any]) -> Command:
        name = attrs.pop("name", None) or f.__name__.lower().replace("_", "-")
        params = cls.collect_params(f)
        help_text = attrs.pop("help", f.__doc__)
        return Command(name=name, callback=f, params=params, help=help_text)

    @classmethod
    def from_group_callback(
        cls, f: Callback, param_decls: Sequence[str], attrs: Dict[str, Any]
    ) -> "Group":
        name = attrs.pop("name", None) or f.__name__.lower().replace("_", "-")
        params = cls.collect_params(f)
        help_text = attrs.pop("help", f.__doc__)
        return Group(name=name, callback=f, params=params, help=help_text)