from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass
from typing import Any, Callable

from .exceptions import Exit
from .params import ArgumentInfo, OptionInfo
from .utils import _first_line, _normalize_command_name, _option_decl_to_dest, convert_value, echo


@dataclass
class _ParamSpec:
    name: str
    kind: str  # "argument" or "option"
    annotation: Any
    required: bool
    default: Any
    help: str | None
    # option
    option_decls: tuple[str, ...] = ()
    is_flag: bool = False


@dataclass
class _Command:
    name: str
    func: Callable[..., Any]
    help: str | None = None


class Typer:
    def __init__(
        self,
        name: str | None = None,
        help: str | None = None,
        add_help_option: bool = True,
        invoke_without_command: bool = False,
        no_args_is_help: bool = False,
    ):
        self.info_name = name
        self.help = help
        self.add_help_option = add_help_option
        self.invoke_without_command = invoke_without_command
        self.no_args_is_help = no_args_is_help
        self._commands: list[_Command] = []
        self._callback: Callable[..., Any] | None = None

    def command(self, name: str | None = None, help: str | None = None):
        def decorator(func: Callable[..., Any]):
            cmd_name = _normalize_command_name(name or func.__name__)
            cmd_help = help if help is not None else _first_line(func.__doc__)
            self._commands.append(_Command(name=cmd_name, func=func, help=cmd_help))
            return func

        return decorator

    def callback(self, name: str | None = None, help: str | None = None):
        # Minimal compatibility: store as root callback
        def decorator(func: Callable[..., Any]):
            self._callback = func
            return func

        return decorator

    def add_typer(self, other: "Typer", name: str | None = None):
        prefix = _normalize_command_name(name or other.info_name or "")
        if not prefix:
            for c in other._commands:
                self._commands.append(c)
        else:
            for c in other._commands:
                self._commands.append(
                    _Command(
                        name=f"{prefix} {c.name}",
                        func=c.func,
                        help=c.help,
                    )
                )
        return other

    def _prog_name(self, prog_name: str | None) -> str:
        if prog_name:
            return prog_name
        if self.info_name:
            return self.info_name
        return "app"

    def _find_command(self, tokens: list[str]) -> tuple[_Command | None, int]:
        # Support "grouped" commands created by add_typer by matching multiple tokens.
        if not tokens:
            return None, 0
        # Find longest match of command.name split by spaces.
        best = None
        best_len = 0
        for c in self._commands:
            parts = c.name.split()
            if len(parts) > len(tokens):
                continue
            if tokens[: len(parts)] == parts and len(parts) > best_len:
                best = c
                best_len = len(parts)
        if best is not None:
            return best, best_len
        # Single token match
        for c in self._commands:
            if c.name == tokens[0]:
                return c, 1
        return None, 0

    def _app_help(self, prog: str) -> str:
        lines: list[str] = []
        lines.append(f"Usage: {prog} [OPTIONS] COMMAND [ARGS]...")
        if self.help:
            lines.append("")
            lines.append(self.help)
        lines.append("")
        lines.append("Commands:")
        if self._commands:
            for c in self._commands:
                desc = c.help or ""
                if desc:
                    lines.append(f"  {c.name}  {desc}")
                else:
                    lines.append(f"  {c.name}")
        else:
            lines.append("  (no commands)")
        if self.add_help_option:
            lines.append("")
            lines.append("Options:")
            lines.append("  --help  Show this message and exit.")
        return "\n".join(lines) + "\n"

    def _command_help(self, prog: str, cmd: _Command) -> str:
        specs = _build_params(cmd.func)
        args_usage = []
        for s in specs:
            if s.kind == "argument":
                token = s.name.upper()
                if not s.required:
                    token = f"[{token}]"
                args_usage.append(token)
        usage = f"Usage: {prog} {cmd.name}"
        if any(s.kind == "option" for s in specs):
            usage += " [OPTIONS]"
        if args_usage:
            usage += " " + " ".join(args_usage)

        lines: list[str] = [usage]
        if cmd.help:
            lines += ["", cmd.help]
        arg_specs = [s for s in specs if s.kind == "argument"]
        opt_specs = [s for s in specs if s.kind == "option"]

        if arg_specs:
            lines.append("")
            lines.append("Arguments:")
            for s in arg_specs:
                desc = s.help or ""
                req = "" if s.required else "  [optional]"
                if desc:
                    lines.append(f"  {s.name.upper()}  {desc}{req}")
                else:
                    lines.append(f"  {s.name.upper()}{req}")

        if opt_specs or self.add_help_option:
            lines.append("")
            lines.append("Options:")
            for s in opt_specs:
                decls = ", ".join(s.option_decls) if s.option_decls else f"--{s.name.replace('_','-')}"
                tail = []
                if s.help:
                    tail.append(s.help)
                if not s.required and s.default is not None and s.default is not ...:
                    tail.append(f"[default: {s.default}]")
                txt = "  " + decls
                if tail:
                    txt += "  " + " ".join(tail)
                lines.append(txt)
            if self.add_help_option:
                lines.append("  --help  Show this message and exit.")
        return "\n".join(lines) + "\n"

    def _parse_and_invoke(self, cmd: _Command, cmd_args: list[str], prog: str) -> int:
        specs = _build_params(cmd.func)
        if any(a in ("--help", "-h") for a in cmd_args):
            echo(self._command_help(prog, cmd), nl=False)
            return 0

        opt_specs = {s.name: s for s in specs if s.kind == "option"}
        arg_specs = [s for s in specs if s.kind == "argument"]

        # Build option lookup by declarations
        decl_map: dict[str, str] = {}
        for s in opt_specs.values():
            for d in (s.option_decls or (f"--{s.name.replace('_','-')}",)):
                decl_map[d] = s.name
            # also allow --no-flag for bool flags default True
            if s.is_flag and isinstance(s.default, bool) and s.default is True:
                decl_map[f"--no-{s.name.replace('_','-')}"] = s.name

        values: dict[str, Any] = {}
        # defaults
        for s in specs:
            if s.default is not ...:
                values[s.name] = s.default

        positionals: list[str] = []
        i = 0
        while i < len(cmd_args):
            tok = cmd_args[i]
            if tok == "--":
                positionals.extend(cmd_args[i + 1 :])
                break
            if tok.startswith("-") and tok != "-":
                # option
                name = None
                val: str | None = None
                if tok.startswith("--") and "=" in tok:
                    k, v = tok.split("=", 1)
                    name = decl_map.get(k)
                    val = v
                else:
                    name = decl_map.get(tok)
                if name is None:
                    echo(f"Error: No such option: {tok}", err=True)
                    return 2
                spec = opt_specs[name]

                # handle negated bool
                if spec.is_flag and tok.startswith("--no-"):
                    values[name] = False
                    i += 1
                    continue

                if spec.is_flag:
                    values[name] = True
                    i += 1
                    continue

                if val is None:
                    if i + 1 >= len(cmd_args):
                        echo(f"Error: Option {tok} requires a value", err=True)
                        return 2
                    val = cmd_args[i + 1]
                    i += 2
                else:
                    i += 1
                try:
                    values[name] = convert_value(val, spec.annotation)
                except Exception:
                    echo(f"Error: Invalid value for {tok}: {val}", err=True)
                    return 2
                continue
            else:
                positionals.append(tok)
                i += 1

        if len(positionals) < sum(1 for s in arg_specs if s.required):
            echo("Error: Missing argument", err=True)
            return 2
        if len(positionals) > len(arg_specs):
            echo("Error: Got unexpected extra argument", err=True)
            return 2

        # bind positional args
        for idx, spec in enumerate(arg_specs):
            if idx < len(positionals):
                raw = positionals[idx]
                try:
                    values[spec.name] = convert_value(raw, spec.annotation)
                except Exception:
                    echo(f"Error: Invalid value for {spec.name}: {raw}", err=True)
                    return 2
            else:
                if spec.required:
                    echo(f"Error: Missing argument {spec.name}", err=True)
                    return 2
                # already defaulted

        # required options
        for s in opt_specs.values():
            if s.required and s.name not in values:
                # show preferred decl
                decl = (s.option_decls[0] if s.option_decls else f"--{s.name.replace('_','-')}")
                echo(f"Error: Missing option {decl}", err=True)
                return 2

        try:
            result = cmd.func(**values)
            if isinstance(result, int):
                return int(result)
            return 0
        except Exit as e:
            return int(e.exit_code)
        except SystemExit as e:
            code = e.code
            if code is None:
                return 0
            if isinstance(code, int):
                return code
            try:
                return int(code)
            except Exception:
                return 1

    def _run(self, args: list[str], prog_name: str | None) -> int:
        prog = self._prog_name(prog_name)
        if any(a in ("--help", "-h") for a in args[:1]) and (args and args[0] in ("--help", "-h")):
            echo(self._app_help(prog), nl=False)
            return 0

        if not args:
            if self.no_args_is_help:
                echo(self._app_help(prog), nl=False)
                return 0
            if self._callback and self.invoke_without_command:
                try:
                    r = self._callback()
                    return int(r) if isinstance(r, int) else 0
                except Exit as e:
                    return int(e.exit_code)
            echo(self._app_help(prog), nl=False)
            return 0

        cmd, consumed = self._find_command(args)
        if cmd is None:
            if args and args[0] in ("--help", "-h"):
                echo(self._app_help(prog), nl=False)
                return 0
            echo(f"Error: No such command: {args[0]}", err=True)
            echo(self._app_help(prog), nl=False)
            return 2

        cmd_args = args[consumed:]
        # run callback if present (minimal)
        if self._callback:
            try:
                r = self._callback()
                if isinstance(r, int) and r != 0:
                    return int(r)
            except Exit as e:
                return int(e.exit_code)
        return self._parse_and_invoke(cmd, cmd_args, prog)

    def __call__(self, args: list[str] | None = None, prog_name: str | None = None) -> int:
        if args is None:
            args = sys.argv[1:]
        return self._run(list(args), prog_name)

    def main(self, args: list[str] | None = None, prog_name: str | None = None, standalone_mode: bool = True):
        if args is None:
            args = sys.argv[1:]
        try:
            code = self._run(list(args), prog_name)
        except Exit as e:
            code = int(e.exit_code)
        except SystemExit as e:
            code = int(e.code) if isinstance(e.code, int) else 1
        except Exception as e:
            echo(str(e), err=True)
            code = 1

        if standalone_mode:
            raise SystemExit(code)
        return code


def _build_params(func: Callable[..., Any]) -> list[_ParamSpec]:
    sig = inspect.signature(func)
    specs: list[_ParamSpec] = []
    for name, p in sig.parameters.items():
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            # not supported in this minimal version
            continue

        annotation = p.annotation if p.annotation is not inspect._empty else str
        default = p.default if p.default is not inspect._empty else ...

        if isinstance(default, OptionInfo):
            info = default
            # Determine declarations
            decls = info.param_decls
            if not decls:
                decls = (f"--{name.replace('_','-')}",)
            # Determine flag
            is_flag = bool(info.is_flag) if info.is_flag is not None else (annotation is bool or info.default in (True, False))
            required = info.default is ...
            specs.append(
                _ParamSpec(
                    name=name,
                    kind="option",
                    annotation=annotation,
                    required=required,
                    default=info.default,
                    help=info.help,
                    option_decls=tuple(decls),
                    is_flag=is_flag,
                )
            )
        else:
            if isinstance(default, ArgumentInfo):
                info = default
                required = info.default is ...
                dflt = info.default
                hlp = info.help
            else:
                required = default is ...
                dflt = default
                hlp = None
            specs.append(
                _ParamSpec(
                    name=name,
                    kind="argument",
                    annotation=annotation,
                    required=required,
                    default=dflt,
                    help=hlp,
                )
            )
    return specs


def run(function: Callable[..., Any]) -> None:
    app = Typer()
    app.command()(function)
    app.main()