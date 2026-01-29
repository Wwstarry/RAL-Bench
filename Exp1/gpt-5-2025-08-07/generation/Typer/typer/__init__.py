import sys
import inspect
import io
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union


__all__ = [
    "Typer",
    "Option",
    "Argument",
    "echo",
    "Exit",
]


class Exit(Exception):
    def __init__(self, code: int = 0):
        super().__init__(code)
        self.code = int(code)


def echo(message: Any = "", err: bool = False, nl: bool = True) -> None:
    text = str(message)
    stream = sys.stderr if err else sys.stdout
    if nl:
        text = text + "\n"
    stream.write(text)
    stream.flush()


class _ParamBase:
    def __init__(self, default: Any = None, *flags: str, help: Optional[str] = None):
        self.default = default
        self.flags = tuple(f for f in flags if isinstance(f, str) and f.startswith("-"))
        self.help = help

    def __repr__(self):
        return f"<{self.__class__.__name__} default={self.default!r} flags={self.flags!r}>"


class Option(_ParamBase):
    pass


class Argument(_ParamBase):
    # Arguments ignore flags; default can mark optional positional
    pass


def _to_param_name(name: str) -> str:
    return name.replace("_", "-")


def _short_and_long_flags(flags: Sequence[str], param_name: str) -> Tuple[Optional[str], Optional[str]]:
    short = None
    long = None
    for f in flags:
        if f.startswith("--"):
            long = f
        elif f.startswith("-"):
            # keep the shortest one as short flag
            if short is None or len(f) < len(short):
                short = f
    if long is None:
        long = "--" + _to_param_name(param_name)
    return short, long


def _convert_value(value: str, annotation: Any) -> Any:
    if annotation is inspect._empty:
        return value
    typ = annotation
    try:
        if typ == bool:
            if isinstance(value, bool):
                return value
            value_lower = str(value).lower()
            if value_lower in ("1", "true", "yes", "on"):
                return True
            if value_lower in ("0", "false", "no", "off"):
                return False
            # fall back: non-empty -> True
            return bool(value)
        return typ(value)
    except Exception:
        # if conversion fails, return raw value
        return value


class _Command:
    def __init__(self, func: Callable, name: str, help: Optional[str] = None):
        self.func = func
        self.name = name
        self.help = help or (func.__doc__.strip().splitlines()[0] if func.__doc__ else "")
        self.signature = inspect.signature(func)
        self.parameters = list(self.signature.parameters.values())
        # Precompute meta for faster parsing
        self._positional_params = []
        self._option_params = []
        for p in self.parameters:
            default = p.default
            if isinstance(default, Option):
                self._option_params.append(p)
            elif isinstance(default, Argument):
                self._positional_params.append(p)
            else:
                # No special default -> positional or optional positional
                self._positional_params.append(p)

    def _param_help(self, p: inspect.Parameter) -> str:
        default = p.default
        if isinstance(default, Option):
            return default.help or ""
        if isinstance(default, Argument):
            return default.help or ""
        return ""

    def _is_bool_option(self, p: inspect.Parameter) -> bool:
        default = p.default
        if isinstance(default, Option):
            if p.annotation is bool:
                return True
            if isinstance(default.default, bool):
                return True
        return False

    def format_usage(self, app_name: str) -> str:
        parts = [f"Usage: {app_name} {self.name}"]
        has_options = any(isinstance(p.default, Option) for p in self.parameters)
        if has_options:
            parts.append("[OPTIONS]")
        # arguments
        for p in self.parameters:
            default = p.default
            if isinstance(default, Option):
                continue
            arg_name = _to_param_name(p.name).upper()
            # required or optional
            required = default is inspect._empty or (isinstance(default, Argument) and default.default is None)
            parts.append(arg_name if required else f"[{arg_name}]")
        parts.append("")
        return " ".join(parts)

    def format_help(self, app_name: str) -> str:
        # Header
        lines = []
        lines.append(self.format_usage(app_name))
        if self.help:
            lines.append("")
            lines.append(self.help)
        # Options
        opt_lines = []
        for p in self.parameters:
            default = p.default
            if isinstance(default, Option):
                short, long = _short_and_long_flags(default.flags, p.name)
                opt_name = (short + ", " if short else "") + (long or "")
                type_desc = "BOOLEAN" if self._is_bool_option(p) else (p.annotation.__name__.upper() if p.annotation is not inspect._empty and p.annotation != bool else "TEXT")
                desc = self._param_help(p)
                if self._is_bool_option(p):
                    opt_lines.append(f"  {opt_name}  {desc}".rstrip())
                else:
                    opt_lines.append(f"  {opt_name} {type_desc}  {desc}".rstrip())
        # Help option
        opt_lines.append("  -h, --help  Show this message and exit.")
        if opt_lines:
            lines.append("")
            lines.append("Options:")
            lines.extend(opt_lines)
        # Arguments
        arg_lines = []
        for p in self.parameters:
            default = p.default
            if isinstance(default, Option):
                continue
            arg_name = _to_param_name(p.name).upper()
            desc = self._param_help(p)
            arg_lines.append(f"  {arg_name}  {desc}".rstrip())
        if arg_lines:
            lines.append("")
            lines.append("Arguments:")
            lines.extend(arg_lines)
        return "\n".join(lines).rstrip() + "\n"

    def parse_and_invoke(self, app_name: str, args: List[str]) -> Tuple[int, Optional[Exception]]:
        # Help for command
        if any(a in ("-h", "--help") for a in args):
            echo(self.format_help(app_name))
            return 0, None

        # Map flags to param names
        flag_to_param: Dict[str, inspect.Parameter] = {}
        expects_value: Dict[str, bool] = {}
        for p in self.parameters:
            default = p.default
            if isinstance(default, Option):
                short, long = _short_and_long_flags(default.flags, p.name)
                for f in (short, long):
                    if f:
                        flag_to_param[f] = p
                        expects_value[f] = not self._is_bool_option(p)

        # Prepare kwargs to pass to function
        kwargs: Dict[str, Any] = {}
        consumed_indices = set()

        # First pass: parse options
        i = 0
        while i < len(args):
            token = args[i]
            if token.startswith("-"):
                # allow --name=value
                if "=" in token and token.startswith("--"):
                    opt, val = token.split("=", 1)
                    p = flag_to_param.get(opt)
                    if not p:
                        echo(f"Error: Unknown option '{opt}'", err=True)
                        return 2, None
                    if expects_value.get(opt, True):
                        kwargs[p.name] = _convert_value(val, p.annotation)
                    else:
                        kwargs[p.name] = _convert_value(val, p.annotation)
                    consumed_indices.add(i)
                    i += 1
                    continue
                p = flag_to_param.get(token)
                if not p:
                    echo(f"Error: Unknown option '{token}'", err=True)
                    return 2, None
                # boolean flag doesn't take following value
                if self._is_bool_option(p):
                    kwargs[p.name] = True
                    consumed_indices.add(i)
                    i += 1
                    continue
                # expect a value next
                if i + 1 >= len(args):
                    echo(f"Error: Option '{token}' requires a value", err=True)
                    return 2, None
                val = args[i + 1]
                kwargs[p.name] = _convert_value(val, p.annotation)
                consumed_indices.add(i)
                consumed_indices.add(i + 1)
                i += 2
            else:
                i += 1

        # Build positional list of remaining args
        remaining: List[str] = [a for idx, a in enumerate(args) if idx not in consumed_indices]

        # Assign positional
        pos_params: List[inspect.Parameter] = []
        for p in self.parameters:
            if isinstance(p.default, Option):
                continue
            pos_params.append(p)

        r_idx = 0
        for p in pos_params:
            default = p.default
            if r_idx < len(remaining):
                value = remaining[r_idx]
                kwargs[p.name] = _convert_value(value, p.annotation)
                r_idx += 1
            else:
                # missing
                if isinstance(default, Argument):
                    if default.default is None:
                        echo(f"Error: Missing argument '{_to_param_name(p.name).upper()}'", err=True)
                        return 2, None
                    else:
                        kwargs[p.name] = default.default
                else:
                    if default is inspect._empty:
                        echo(f"Error: Missing argument '{_to_param_name(p.name).upper()}'", err=True)
                        return 2, None
                    else:
                        kwargs[p.name] = default

        # For options not provided
        for p in self.parameters:
            if not isinstance(p.default, Option):
                continue
            if p.name in kwargs:
                continue
            default = p.default
            if self._is_bool_option(p):
                # bool default fallback
                if isinstance(default.default, bool):
                    kwargs[p.name] = default.default
                elif p.annotation is bool:
                    kwargs[p.name] = False
                else:
                    kwargs[p.name] = False
            else:
                if default.default is None and p.annotation is not bool:
                    # required option without default
                    echo(f"Error: Missing option '--{_to_param_name(p.name)}'", err=True)
                    return 2, None
                kwargs[p.name] = default.default

        # Invoke
        try:
            result = self.func(**kwargs)
            if isinstance(result, int):
                return int(result), None
            return 0, None
        except Exit as e:
            return e.code, e
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
            return int(code), e
        except Exception as e:
            echo(f"Error: {e}", err=True)
            return 1, e


class Typer:
    def __init__(self, name: Optional[str] = None, help: Optional[str] = None):
        self.name = name or "app"
        self.help = help or ""
        self._commands: Dict[str, _Command] = {}

    def command(self, name: Optional[str] = None, help: Optional[str] = None) -> Callable[[Callable], Callable]:
        def decorator(func: Callable) -> Callable:
            cmd_name = name or func.__name__.replace("_", "-")
            self._commands[cmd_name] = _Command(func, cmd_name, help=help)
            return func
        return decorator

    def add_typer(self, typer_obj: "Typer", name: Optional[str] = None, help: Optional[str] = None):
        # Minimal support for nesting: mount commands under a group name
        group_name = name or typer_obj.name
        for cmd_name, cmd in typer_obj._commands.items():
            full_name = f"{group_name} {cmd_name}"
            self._commands[full_name] = cmd

    def _format_global_usage(self) -> str:
        return f"Usage: {self.name} [COMMAND] [ARGS]...\n"

    def _format_commands_list(self) -> str:
        lines = ["Commands:"]
        # Show direct commands (non-nested first)
        for cmd_name in sorted(self._commands.keys()):
            # Only top-level names (no spaces) appear as commands; nested groups appear as group commands
            display_name = cmd_name
            if " " in cmd_name:
                # skip nested direct display in global list
                continue
            help_text = self._commands[cmd_name].help
            if help_text:
                lines.append(f"  {display_name}  {help_text}")
            else:
                lines.append(f"  {display_name}")
        lines.append("  -h, --help  Show this message and exit.")
        return "\n".join(lines) + "\n"

    def format_help(self) -> str:
        parts = [self._format_global_usage()]
        if self.help:
            parts.append(self.help + "\n")
        parts.append(self._format_commands_list())
        return "".join(parts)

    def _resolve_command(self, args: List[str]) -> Tuple[Optional[_Command], List[str], Optional[str]]:
        if not args:
            return None, [], None
        # Support nested commands "group subcmd" when registered via add_typer
        candidate = args[0]
        if candidate in ("-h", "--help"):
            return None, args[1:], "help"
        # Try exact match on first token
        if candidate in self._commands:
            return self._commands[candidate], args[1:], candidate
        # Try nested: first two tokens make full name
        if len(args) >= 2:
            two = f"{args[0]} {args[1]}"
            if two in self._commands:
                return self._commands[two], args[2:], two
        return None, args[1:], candidate

    def _run(self, args: Optional[List[str]] = None) -> Tuple[int, Optional[Exception]]:
        argv = list(args or [])
        # Global help
        if not argv or argv[0] in ("-h", "--help"):
            echo(self.format_help())
            return 0, None
        cmd, remaining, name = self._resolve_command(argv)
        if cmd is None:
            echo(f"Error: No such command '{name}'", err=True)
            return 2, None
        return cmd.parse_and_invoke(self.name, remaining)

    def __call__(self, args: Optional[List[str]] = None) -> int:
        code, _ = self._run(args=args)
        return code