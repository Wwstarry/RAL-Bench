import sys
import inspect
import functools
import typing
import shlex

class Exit(SystemExit):
    def __init__(self, code: int = 0):
        super().__init__(code)
        self.code = code

def echo(message: typing.Any = "", file=None, nl: bool = True, err: bool = False):
    if file is None:
        file = sys.stderr if err else sys.stdout
    print(message, file=file, end="\n" if nl else "")

class Option:
    def __init__(self, default=..., *, help: str = None, show_default: bool = True):
        self.default = default
        self.help = help
        self.show_default = show_default

class Argument:
    def __init__(self, default=..., *, help: str = None):
        self.default = default
        self.help = help

def _get_param_info(param: inspect.Parameter):
    # Returns a tuple (name, kind, default, annotation)
    return param.name, param.kind, param.default, param.annotation

def _is_option(param: inspect.Parameter):
    # We treat parameters with default values as options, else arguments
    return param.default != inspect.Parameter.empty

def _format_default(value):
    if isinstance(value, str):
        return f'"{value}"'
    return str(value)

def _format_help_param(name, param, is_option):
    help_text = ""
    if is_option:
        if param.help:
            help_text += param.help
        if param.default != inspect.Parameter.empty and param.default is not None:
            if param.show_default:
                help_text += f" (default: {_format_default(param.default)})"
    else:
        if param.help:
            help_text += param.help
    return help_text

def _parse_args(args, params):
    # params: list of (name, kind, default, annotation, param_obj)
    # returns dict of param_name: value
    # args is list of strings (command line args)
    # We support options as --name value or --name=value, and flags (bool)
    # Positional arguments are assigned in order
    values = {}
    # Prepare param lookup
    param_map = {p[0]: p for p in params}
    # Separate positional and options
    positional_params = [p for p in params if p[1] in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY) and p[2] == inspect.Parameter.empty]
    option_params = {p[0]: p for p in params if p[2] != inspect.Parameter.empty}

    # For bool options, default is False if default is False or True
    # We'll treat bool options specially: if present, True, else False

    # Parse args
    # We'll iterate over args and parse options first
    # Then assign positional args in order

    # Map from option name to param name
    option_names = {}
    for name, kind, default, annotation, param_obj in option_params.values():
        option_names[f"--{name.replace('_','-')}"] = name

    # Parsed options
    parsed_options = {}
    # Positional args values
    positional_values = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            # End of options
            i += 1
            positional_values.extend(args[i:])
            break
        elif arg.startswith("--"):
            # Option
            if "=" in arg:
                opt, val = arg.split("=", 1)
                if opt not in option_names:
                    raise ValueError(f"Unknown option: {opt}")
                param_name = option_names[opt]
                parsed_options[param_name] = val
                i += 1
            else:
                opt = arg
                if opt not in option_names:
                    raise ValueError(f"Unknown option: {opt}")
                param_name = option_names[opt]
                param_info = option_params[param_name]
                # Check if bool
                if param_info[3] == bool:
                    parsed_options[param_name] = True
                    i += 1
                else:
                    i += 1
                    if i >= len(args):
                        raise ValueError(f"Option {opt} requires a value")
                    parsed_options[param_name] = args[i]
                    i += 1
        else:
            positional_values.append(arg)
            i += 1

    # Assign positional args
    if len(positional_values) > len(positional_params):
        raise ValueError("Too many positional arguments")

    for idx, val in enumerate(positional_values):
        param_name = positional_params[idx][0]
        parsed_options[param_name] = val

    # Fill defaults for options and arguments
    for name, kind, default, annotation, param_obj in params:
        if name not in parsed_options:
            if default != inspect.Parameter.empty:
                parsed_options[name] = default
            else:
                raise ValueError(f"Missing required argument: {name}")

    # Convert types
    for name, kind, default, annotation, param_obj in params:
        val = parsed_options[name]
        if annotation != inspect.Parameter.empty and val is not None:
            try:
                if annotation == bool:
                    # Already handled bool options as True if present, else default False
                    # But if val is string, convert
                    if isinstance(val, str):
                        val_lower = val.lower()
                        if val_lower in ("true", "1", "yes", "on"):
                            val = True
                        elif val_lower in ("false", "0", "no", "off"):
                            val = False
                        else:
                            val = bool(val)
                else:
                    val = annotation(val)
            except Exception:
                # fallback: keep original val
                pass
            parsed_options[name] = val

    return parsed_options

class Typer:
    def __init__(self):
        self.commands = {}
        self._ctx = None

    def command(self, name=None):
        def decorator(f):
            cmd_name = name or f.__name__
            self.add_command(f, cmd_name)
            return f
        return decorator

    def add_command(self, callback, name=None):
        cmd_name = name or callback.__name__
        if cmd_name in self.commands:
            raise RuntimeError(f"Command {cmd_name} already exists")
        self.commands[cmd_name] = callback

    def _get_command_help(self, callback):
        # Compose help text for a command
        doc = callback.__doc__ or ""
        doc = doc.strip()
        sig = inspect.signature(callback)
        params = []
        for param in sig.parameters.values():
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            if param.default != inspect.Parameter.empty:
                if isinstance(param.default, Option):
                    default = param.default.default
                    help_text = param.default.help
                    show_default = param.default.show_default
                else:
                    default = param.default
                    help_text = None
                    show_default = True
                p = Option(default=default, help=help_text, show_default=show_default)
                params.append((param.name, p))
            else:
                if isinstance(param.default, Argument):
                    p = param.default
                else:
                    p = Argument()
                params.append((param.name, p))
        # Format usage line
        usage_parts = []
        for name, p in params:
            if isinstance(p, Option):
                usage_parts.append(f"[--{name.replace('_','-')} <value>]")
            else:
                usage_parts.append(f"<{name}>")
        usage = " ".join(usage_parts)
        help_lines = []
        if doc:
            help_lines.append(doc)
        if params:
            help_lines.append("")
            help_lines.append("Arguments:")
            for name, p in params:
                line = f"  {name}"
                if isinstance(p, Option):
                    line = f"  --{name.replace('_','-')}"
                if p.help:
                    line += f"\t{p.help}"
                if isinstance(p, Option) and p.default != ... and p.show_default:
                    line += f" (default: {_format_default(p.default)})"
                help_lines.append(line)
        return usage, "\n".join(help_lines)

    def _print_help(self, prog_name):
        echo(f"Usage: {prog_name} [OPTIONS] COMMAND [ARGS]...")
        echo("")
        echo("Commands:")
        max_len = max((len(cmd) for cmd in self.commands), default=0)
        for cmd in sorted(self.commands):
            callback = self.commands[cmd]
            doc = callback.__doc__ or ""
            first_line = doc.strip().splitlines()[0] if doc else ""
            echo(f"  {cmd.ljust(max_len)}  {first_line}")
        echo("")
        echo("Options:")
        echo("  --help  Show this message and exit.")

    def _print_command_help(self, prog_name, command_name):
        if command_name not in self.commands:
            echo(f"Error: No such command '{command_name}'")
            raise Exit(2)
        callback = self.commands[command_name]
        usage, help_text = self._get_command_help(callback)
        echo(f"Usage: {prog_name} {command_name} {usage}")
        echo("")
        if help_text:
            echo(help_text)
        echo("")
        echo("Options:")
        echo("  --help  Show this message and exit.")

    def _run_command(self, command_name, args):
        if command_name not in self.commands:
            echo(f"Error: No such command '{command_name}'", err=True)
            raise Exit(2)
        callback = self.commands[command_name]
        sig = inspect.signature(callback)
        params = []
        for param in sig.parameters.values():
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            # Wrap default in Option or Argument if not already
            if param.default != inspect.Parameter.empty:
                if isinstance(param.default, (Option, Argument)):
                    default = param.default
                else:
                    default = Option(param.default)
                params.append((param.name, param.kind, default.default, param.annotation, default))
            else:
                params.append((param.name, param.kind, inspect.Parameter.empty, param.annotation, Argument()))
        try:
            parsed = _parse_args(args, params)
        except ValueError as e:
            echo(f"Error: {e}", err=True)
            raise Exit(2)
        try:
            result = callback(**parsed)
            if isinstance(result, int):
                raise Exit(result)
            elif result is None:
                raise Exit(0)
            else:
                raise Exit(0)
        except Exit as e:
            raise e
        except Exception as e:
            echo(f"Error: {e}", err=True)
            raise Exit(1)

    def __call__(self, args=None):
        # args: list of strings or None (default sys.argv[1:])
        if args is None:
            args = sys.argv[1:]
        prog_name = sys.argv[0] if sys.argv else "app"
        if not args or args[0] in ("--help", "-h"):
            self._print_help(prog_name)
            raise Exit(0)
        first = args[0]
        if first in self.commands:
            # Check if next arg is --help or -h
            if len(args) > 1 and args[1] in ("--help", "-h"):
                self._print_command_help(prog_name, first)
                raise Exit(0)
            self._run_command(first, args[1:])
        else:
            # Unknown command or no commands defined
            if first.startswith("-"):
                # Possibly global options (not supported)
                self._print_help(prog_name)
                raise Exit(0)
            else:
                echo(f"Error: Unknown command '{first}'", err=True)
                self._print_help(prog_name)
                raise Exit(2)