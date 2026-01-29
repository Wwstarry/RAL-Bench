from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from .testing import Result  # re-exported behavior via CliRunner uses this
from .utils import echo


class Exit(Exception):
    def __init__(self, code: int = 0) -> None:
        super().__init__(code)
        self.code = int(code)


@dataclass
class OptionInfo:
    default: Any = None
    help: Optional[str] = None
    param_decls: Optional[Sequence[str]] = None  # e.g. ("--name", "-n")
    show_default: bool = True


@dataclass
class ArgumentInfo:
    default: Any = ...
    help: Optional[str] = None


def Option(
    default: Any = None,
    *param_decls: str,
    help: Optional[str] = None,
    show_default: bool = True,
) -> OptionInfo:
    decls = list(param_decls) if param_decls else None
    return OptionInfo(default=default, help=help, param_decls=decls, show_default=show_default)


def Argument(
    default: Any = ...,
    help: Optional[str] = None,
) -> ArgumentInfo:
    return ArgumentInfo(default=default, help=help)


def _is_option_default(obj: Any) -> bool:
    return isinstance(obj, OptionInfo)


def _is_argument_default(obj: Any) -> bool:
    return isinstance(obj, ArgumentInfo)


def _annotation_to_type(ann: Any) -> Any:
    if ann is inspect._empty:
        return str
    origin = getattr(ann, "__origin__", None)
    if origin is Union:
        args = [a for a in getattr(ann, "__args__", ()) if a is not type(None)]
        if args:
            return args[0]
        return str
    return ann


def _coerce(value: str, typ: Any) -> Any:
    if typ is bool:
        v = value.lower()
        if v in ("1", "true", "t", "yes", "y", "on"):
            return True
        if v in ("0", "false", "f", "no", "n", "off"):
            return False
        raise ValueError(f"Invalid boolean value: {value}")
    if typ is int:
        return int(value)
    if typ is float:
        return float(value)
    return value


class _Command:
    def __init__(self, name: str, func: Callable[..., Any], help: Optional[str] = None) -> None:
        self.name = name
        self.func = func
        self.help = help or (inspect.getdoc(func) or "").splitlines()[0] if inspect.getdoc(func) else ""
        self.signature = inspect.signature(func)

        self.params = list(self.signature.parameters.values())

        self.options: List[Tuple[str, inspect.Parameter, OptionInfo]] = []
        self.arguments: List[Tuple[str, inspect.Parameter, ArgumentInfo]] = []

        for p in self.params:
            default = p.default
            if _is_option_default(default):
                info: OptionInfo = default
                self.options.append((p.name, p, info))
            elif _is_argument_default(default):
                info: ArgumentInfo = default
                self.arguments.append((p.name, p, info))
            else:
                # Bare required positional argument
                self.arguments.append((p.name, p, ArgumentInfo(default=default if default is not inspect._empty else ...)))

    def _option_flags(self, param_name: str, info: OptionInfo) -> List[str]:
        if info.param_decls:
            return list(info.param_decls)
        flag = "--" + param_name.replace("_", "-")
        return [flag]

    def format_help(self, prog: str, app_name: str, is_subcommand: bool = True) -> str:
        usage_parts = [prog]
        if is_subcommand:
            usage_parts.append(self.name)

        # Add options placeholder
        if self.options:
            usage_parts.append("[OPTIONS]")

        # Add arguments
        for arg_name, p, info in self.arguments:
            if info.default is ... and p.default is inspect._empty:
                usage_parts.append(f"{arg_name.upper()}")
            else:
                usage_parts.append(f"[{arg_name.upper()}]")

        lines: List[str] = []
        lines.append(f"Usage: {' '.join(usage_parts)}")
        if self.help:
            lines.append("")
            lines.append(self.help)

        if self.arguments:
            lines.append("")
            lines.append("Arguments:")
            for arg_name, p, info in self.arguments:
                req = (info.default is ... and p.default is inspect._empty)
                desc = (info.help or "").strip()
                meta = "required" if req else "optional"
                lines.append(f"  {arg_name.upper():<14} {meta}{('  ' + desc) if desc else ''}")

        if self.options:
            lines.append("")
            lines.append("Options:")
            lines.append(f"  {'--help':<14} Show this message and exit.")
            for opt_name, p, info in self.options:
                flags = ", ".join(self._option_flags(opt_name, info))
                ann = _annotation_to_type(p.annotation)
                default = info.default
                desc = (info.help or "").strip()
                default_txt = ""
                if info.show_default and default is not None and default is not inspect._empty:
                    default_txt = f" [default: {default}]"
                # bool options: show as flag
                if ann is bool and isinstance(default, bool):
                    lines.append(f"  {flags:<14} {desc}{default_txt}".rstrip())
                else:
                    lines.append(f"  {flags + ' TEXT':<14} {desc}{default_txt}".rstrip())

        return "\n".join(lines) + "\n"

    def invoke(self, argv: Sequence[str], prog: str, app_name: str) -> Result:
        stdout_chunks: List[str] = []
        stderr_chunks: List[str] = []

        def _echo_capture(message: Any = "", nl: bool = True, err: bool = False) -> None:
            text = "" if message is None else str(message)
            if nl:
                text += "\n"
            (stderr_chunks if err else stdout_chunks).append(text)

        # Parse help
        if any(a in ("--help", "-h") for a in argv):
            return Result(
                stdout=self.format_help(prog=prog, app_name=app_name, is_subcommand=True),
                stderr="",
                exit_code=0,
                exception=None,
            )

        # Build defaults
        values: Dict[str, Any] = {}
        for name, p, info in self.options:
            values[name] = info.default
        for name, p, info in self.arguments:
            if info.default is ...:
                # will require a value unless param has real default
                if p.default is not inspect._empty:
                    values[name] = p.default
            else:
                values[name] = info.default

        # Map flags to option param name
        flag_to_name: Dict[str, str] = {}
        for name, p, info in self.options:
            for fl in self._option_flags(name, info):
                flag_to_name[fl] = name

        positionals: List[str] = []
        i = 0
        while i < len(argv):
            token = argv[i]
            if token == "--":
                positionals.extend(list(argv[i + 1 :]))
                break
            if token.startswith("--") and "=" in token:
                flag, val = token.split("=", 1)
                if flag in flag_to_name:
                    opt_name = flag_to_name[flag]
                    param = dict((n, pp) for (n, pp, _) in self.options)[opt_name]
                    ann = _annotation_to_type(param.annotation)
                    try:
                        values[opt_name] = _coerce(val, ann)
                    except Exception as e:
                        stderr_chunks.append(f"Error: Invalid value for {flag}: {e}\n")
                        return Result("".join(stdout_chunks), "".join(stderr_chunks), 2, None)
                else:
                    stderr_chunks.append(f"Error: No such option: {flag}\n")
                    return Result("".join(stdout_chunks), "".join(stderr_chunks), 2, None)
                i += 1
                continue

            if token.startswith("-") and token != "-":
                if token in ("-h", "--help"):
                    return Result(
                        stdout=self.format_help(prog=prog, app_name=app_name, is_subcommand=True),
                        stderr="",
                        exit_code=0,
                        exception=None,
                    )
                if token in flag_to_name:
                    opt_name = flag_to_name[token]
                    param = dict((n, pp) for (n, pp, _) in self.options)[opt_name]
                    info = dict((n, ii) for (n, _, ii) in self.options)[opt_name]
                    ann = _annotation_to_type(param.annotation)
                    if ann is bool and isinstance(info.default, bool):
                        values[opt_name] = True
                        i += 1
                        continue
                    if i + 1 >= len(argv):
                        stderr_chunks.append(f"Error: Option {token} requires a value\n")
                        return Result("".join(stdout_chunks), "".join(stderr_chunks), 2, None)
                    val = argv[i + 1]
                    try:
                        values[opt_name] = _coerce(val, ann)
                    except Exception as e:
                        stderr_chunks.append(f"Error: Invalid value for {token}: {e}\n")
                        return Result("".join(stdout_chunks), "".join(stderr_chunks), 2, None)
                    i += 2
                    continue
                else:
                    # allow combined short flags? not needed; error out
                    stderr_chunks.append(f"Error: No such option: {token}\n")
                    return Result("".join(stdout_chunks), "".join(stderr_chunks), 2, None)

            # positional
            positionals.append(token)
            i += 1

        # Assign positionals to arguments in order
        arg_params = self.arguments
        pos_i = 0
        for arg_name, p, info in arg_params:
            if pos_i < len(positionals):
                ann = _annotation_to_type(p.annotation)
                try:
                    values[arg_name] = _coerce(positionals[pos_i], ann)
                except Exception as e:
                    stderr_chunks.append(f"Error: Invalid value for {arg_name}: {e}\n")
                    return Result("".join(stdout_chunks), "".join(stderr_chunks), 2, None)
                pos_i += 1
            else:
                # no positional left
                if arg_name not in values:
                    # required
                    stderr_chunks.append(f"Error: Missing argument: {arg_name}\n")
                    return Result("".join(stdout_chunks), "".join(stderr_chunks), 2, None)

        if pos_i < len(positionals):
            stderr_chunks.append("Error: Got unexpected extra arguments\n")
            return Result("".join(stdout_chunks), "".join(stderr_chunks), 2, None)

        # Invoke function, capturing echo
        from . import utils as _utils  # local to avoid cycle

        old_echo = _utils.echo
        _utils.echo = _echo_capture
        try:
            try:
                rv = self.func(**values)
            except Exit as e:
                return Result("".join(stdout_chunks), "".join(stderr_chunks), int(e.code), e)
            except SystemExit as e:
                code = int(e.code) if e.code is not None else 0
                return Result("".join(stdout_chunks), "".join(stderr_chunks), code, e)
            except Exception as e:
                # mimic click/typer: non-zero exit; include exception text in stderr
                stderr_chunks.append(f"Error: {e}\n")
                return Result("".join(stdout_chunks), "".join(stderr_chunks), 1, e)

            # Interpret return values: None => 0, int => that code
            exit_code = 0
            if isinstance(rv, int):
                exit_code = int(rv)
            return Result("".join(stdout_chunks), "".join(stderr_chunks), exit_code, None)
        finally:
            _utils.echo = old_echo


class Typer:
    def __init__(self, *, name: Optional[str] = None, help: Optional[str] = None, add_completion: bool = False) -> None:
        self.name = name
        self.help = help or ""
        self.add_completion = add_completion
        self._commands: Dict[str, _Command] = {}
        self._callback: Optional[Callable[..., Any]] = None

    def command(self, name: Optional[str] = None, help: Optional[str] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            cmd_name = name or func.__name__.replace("_", "-")
            self._commands[cmd_name] = _Command(cmd_name, func, help=help)
            return func

        return decorator

    def callback(self, *, invoke_without_command: bool = False) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._callback = func
            return func

        return decorator

    @property
    def registered_commands(self) -> Dict[str, Callable[..., Any]]:
        return {k: v.func for k, v in self._commands.items()}

    def _format_main_help(self, prog: str) -> str:
        lines: List[str] = []
        lines.append(f"Usage: {prog} [OPTIONS] COMMAND [ARGS]...")
        if self.help:
            lines.append("")
            lines.append(self.help)

        lines.append("")
        lines.append("Options:")
        lines.append(f"  {'--help':<14} Show this message and exit.")

        lines.append("")
        lines.append("Commands:")
        if self._commands:
            for name in sorted(self._commands):
                cmd = self._commands[name]
                help_txt = cmd.help or ""
                lines.append(f"  {name:<14} {help_txt}".rstrip())
        return "\n".join(lines) + "\n"

    def _dispatch(self, argv: Sequence[str], prog: str) -> Result:
        argv = list(argv)

        if not argv or argv[0] in ("--help", "-h"):
            return Result(self._format_main_help(prog), "", 0, None)

        cmd_name = argv[0]
        if cmd_name in self._commands:
            cmd = self._commands[cmd_name]
            return cmd.invoke(argv[1:], prog=prog, app_name=prog)
        # unknown command
        if cmd_name.startswith("-"):
            # unknown option at app level
            return Result("", f"Error: No such option: {cmd_name}\n", 2, None)
        return Result("", f"Error: No such command: {cmd_name}\n", 2, None)

    def __call__(self, args: Optional[Sequence[str]] = None, prog_name: Optional[str] = None) -> None:
        if args is None:
            args = sys.argv[1:]
        prog = prog_name or (self.name or (sys.argv[0] if sys.argv else "app"))
        res = self._dispatch(args, prog=prog)
        if res.stdout:
            sys.stdout.write(res.stdout)
        if res.stderr:
            sys.stderr.write(res.stderr)
        raise SystemExit(res.exit_code)