import sys
import inspect
from .params import Option, Argument
from .utils import echo

class Exit(Exception):
    def __init__(self, code=0):
        self.exit_code = code

class Command:
    def __init__(self, name, callback, help=None):
        self.name = name
        self.callback = callback
        self.help = help

class Typer:
    def __init__(self, *, name=None, help=None):
        self._commands = {}
        self._name = name
        self._help = help

    def command(self, name=None, help=None):
        def decorator(func):
            cmd_name = name or func.__name__.replace("_", "-")
            self.add_command(func, name=cmd_name, help=help)
            return func
        return decorator

    def add_command(self, func, name=None, help=None):
        cmd_name = name or func.__name__.replace("_", "-")
        self._commands[cmd_name] = Command(cmd_name, func, help=help)

    def __call__(self, *args, **kwargs):
        return self._main(args=sys.argv[1:])

    def _main(self, args=None):
        if args is None:
            args = sys.argv[1:]

        if not self._commands:
            # Single command mode
            return self._run_command(self._get_single_command(), args)
        else:
            if not args or (args and args[0] in ("-h", "--help")):
                self._print_help()
                return 0
            cmd_name = args[0]
            if cmd_name not in self._commands:
                echo(f"Error: No such command '{cmd_name}'.", err=True)
                sys.exit(2)
            return self._run_command(self._commands[cmd_name], args[1:])

    def _get_single_command(self):
        # Used when Typer is used as a single command app (no .command() used)
        # Find the main function (the first non-dunder function in __main__)
        # For compatibility, we assume the user decorated a function with @app.command or called app.add_command
        if self._commands:
            # There is only one command
            return list(self._commands.values())[0]
        raise RuntimeError("No command registered.")

    def _run_command(self, command, args):
        func = command.callback
        sig = inspect.signature(func)
        params = list(sig.parameters.values())
        parsed_args = []
        parsed_kwargs = {}

        # Parse CLI args to function parameters
        cli_args = list(args)
        i = 0
        for param in params:
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
            default = param.default
            is_option = isinstance(default, Option)
            is_argument = isinstance(default, Argument) or (default == inspect.Parameter.empty)
            if is_option:
                # Option: look for --name or -n
                opt = default
                value = opt.default
                found = False
                for j, arg in enumerate(cli_args):
                    if arg == f"--{param.name.replace('_', '-')}":
                        if opt.is_flag:
                            value = True
                            cli_args.pop(j)
                        else:
                            try:
                                value = param_type(cli_args[j+1])
                                cli_args.pop(j+1)
                                cli_args.pop(j)
                            except (IndexError, ValueError):
                                echo(f"Error: Option --{param.name} requires a value.", err=True)
                                sys.exit(2)
                        found = True
                        break
                    elif opt.short and arg == f"-{opt.short}":
                        if opt.is_flag:
                            value = True
                            cli_args.pop(j)
                        else:
                            try:
                                value = param_type(cli_args[j+1])
                                cli_args.pop(j+1)
                                cli_args.pop(j)
                            except (IndexError, ValueError):
                                echo(f"Error: Option -{opt.short} requires a value.", err=True)
                                sys.exit(2)
                        found = True
                        break
                parsed_kwargs[param.name] = value
            elif is_argument:
                # Argument: take next positional
                if i < len(cli_args):
                    try:
                        value = param_type(cli_args[i])
                    except Exception:
                        value = cli_args[i]
                    parsed_args.append(value)
                    i += 1
                elif default != inspect.Parameter.empty:
                    parsed_args.append(default)
                else:
                    echo(f"Error: Missing argument '{param.name}'.", err=True)
                    sys.exit(2)
            else:
                # Should not happen
                parsed_args.append(None)

        try:
            result = func(*parsed_args, **parsed_kwargs)
        except Exit as e:
            sys.exit(e.exit_code)
        except SystemExit as e:
            sys.exit(e.code)
        return_code = 0
        if isinstance(result, int):
            return_code = result
        sys.exit(return_code)

    def _print_help(self):
        prog = self._name or (sys.argv[0] if sys.argv else "app")
        if self._help:
            echo(self._help)
        echo(f"Usage: {prog} [OPTIONS] COMMAND [ARGS]...")
        if self._commands:
            echo("\nCommands:")
            for name, cmd in self._commands.items():
                help_text = cmd.help or ""
                echo(f"  {name}\t{help_text}")