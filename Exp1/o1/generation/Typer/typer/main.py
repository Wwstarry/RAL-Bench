import sys
import textwrap

class Exit(Exception):
    """Raise this exception to exit the application with a specific status code."""

    def __init__(self, code: int = 0) -> None:
        super().__init__()
        self.exit_code = code


def echo(message: str = "", nl: bool = True):
    """Write text to the console."""
    end = "\n" if nl else ""
    print(message, end=end)


class Argument:
    """
    Metadata for a command argument.
    Used to declare positional parameters to a command function.
    """

    def __init__(self, default=None, help=None):
        self.default = default
        self.help = help


class Option:
    """
    Metadata for a command option.
    Used to declare named parameters (e.g., --option) to a command function.
    """

    def __init__(self, default=None, help=None):
        self.default = default
        self.help = help


class _CommandInfo:
    """Stores information about a command, including its function and parameter definitions."""

    def __init__(self, name, func, help_text=None):
        self.name = name
        self.func = func
        self.help = help_text or ""
        self.arguments = []
        self.options = []
        # Inspect the annotation or default values that might have been assigned
        # via decorators (Argument/Option). We'll store them so we know how
        # to parse them later.
        if not hasattr(self.func, "__typer_params__"):
            self.func.__typer_params__ = []

        for p in self.func.__typer_params__:
            if isinstance(p["type"], Argument):
                self.arguments.append(p)
            elif isinstance(p["type"], Option):
                self.options.append(p)


class Typer:
    """
    Main class for creating a CLI application.
    Use @app.command() to register subcommands, then call app() to run.
    """

    def __init__(self, name=None, help=None):
        self._commands = {}
        self._name = name if name else ""
        self._help = help if help else ""

    def command(self, name=None, help=None):
        """
        Decorator to register a new command.
        Usage:
            @app.command()
            def main(...):
                ...
        """
        def decorator(f):
            cmd_name = name or f.__name__
            self._commands[cmd_name] = _CommandInfo(cmd_name, f, help)
            return f
        return decorator

    def __call__(self):
        """Run the CLI application."""
        self._main(sys.argv[1:])

    def _print_help(self):
        # Print application-level help.
        app_name = self._name if self._name else "Application"
        echo(f"{app_name}\n")
        if self._help:
            echo(textwrap.dedent(self._help).strip())
            echo("")
        echo("Usage:")
        echo(f"  {sys.argv[0]} [OPTIONS] COMMAND [ARGS]...")
        echo("")
        echo("Commands:")
        for cmd_name, cmd_info in self._commands.items():
            if cmd_info.help:
                echo(f"  {cmd_name:15} {cmd_info.help}")
            else:
                echo(f"  {cmd_name}")
        echo("")

    def _print_command_help(self, cmd_name, cmd_info):
        # Print help for a specific command.
        help_text = cmd_info.help or ""
        echo(f"Usage: {sys.argv[0]} {cmd_name}", nl=False)
        for arg in cmd_info.arguments:
            # Show each argument in help as <name>
            echo(f" <{arg['param_name']}>", nl=False)
        for opt in cmd_info.options:
            # Show each option in help as [--name]
            echo(f" [--{opt['param_name']}]", nl=False)
        echo("")
        if help_text:
            echo("")
            echo(textwrap.dedent(help_text).strip())
        echo("")

    def _main(self, args):
        # If no args or '--help' is present, print high-level help
        if not args or ("--help" in args):
            if not args or (args and args[0] != "--help"):
                # If no command given, show app-level help
                self._print_help()
            else:
                # If user typed `COMMAND --help` but there's no command,
                # just print the high-level help
                self._print_help()
            sys.exit(0)

        cmd_name = args[0]
        cmd_info = self._commands.get(cmd_name)
        if not cmd_info:
            echo(f"Error: No such command '{cmd_name}'.")
            sys.exit(1)

        # If the user typed something like: myapp command --help
        # We need to check if "--help" is in the rest of the args before parsing
        if "--help" in args[1:]:
            self._print_command_help(cmd_name, cmd_info)
            sys.exit(0)

        # Collect the remaining args
        cmd_args = args[1:]
        # Build a simple parser to match arguments and options
        # We'll do it in a naive way. The order is arguments first, then options.
        parsed_args = []
        parsed_kwargs = {}

        # We'll fill from left to right for arguments
        arg_index = 0
        skip_next = False

        # Identify recognized long options
        recognized_options = {f"--{opt['param_name']}": opt for opt in cmd_info.options}

        # We'll do minimal parsing. For argument count, we take as many as exist in definitions.
        for i, token in enumerate(cmd_args):
            if skip_next:
                skip_next = False
                continue

            if token.startswith("--"):
                # It's an option
                opt_def = recognized_options.get(token)
                if not opt_def:
                    echo(f"Error: Unknown option '{token}'.")
                    sys.exit(1)
                # Next token is the value (unless we wanted to support booleans, omitted for simplicity)
                if i + 1 >= len(cmd_args):
                    echo(f"Error: Missing value for option '{token}'.")
                    sys.exit(1)
                value = cmd_args[i + 1]
                parsed_kwargs[opt_def["param_name"]] = value
                skip_next = True
            else:
                # It's an argument
                if arg_index < len(cmd_info.arguments):
                    parsed_args.append(token)
                    arg_index += 1
                else:
                    # If we have more positional args than needed, might be an error or might ignore
                    # We'll treat it as error to mimic basic Typer usage
                    echo(f"Error: Unexpected extra argument '{token}'.")
                    sys.exit(1)

        # Fill defaults for missing arguments
        for i, arg_def in enumerate(cmd_info.arguments):
            if i >= len(parsed_args):
                # Use default if any
                if arg_def["type"].default is not None:
                    parsed_args.append(arg_def["type"].default)
                else:
                    echo(f"Error: Missing required argument '{arg_def['param_name']}'.")
                    sys.exit(1)

        # Fill defaults for missing options
        for opt_def in cmd_info.options:
            if opt_def["param_name"] not in parsed_kwargs:
                if opt_def["type"].default is not None:
                    parsed_kwargs[opt_def["param_name"]] = opt_def["type"].default
                else:
                    # If an option has no default but wasn't provided, typically it's None
                    parsed_kwargs[opt_def["param_name"]] = None

        # Invoke command function
        try:
            result = cmd_info.func(*parsed_args, **parsed_kwargs)
        except Exit as e:
            sys.exit(e.exit_code)
        if isinstance(result, int):
            sys.exit(result)
        else:
            sys.exit(0)


def _store_param_info(func, param_name, param_def):
    """Utility to store parameter definitions on a function."""
    if not hasattr(func, "__typer_params__"):
        func.__typer_params__ = []
    func.__typer_params__.append({"param_name": param_name, "type": param_def})


def ArgumentDecorator(default=None, help=None):
    """
    Decorator used to annotate a function parameter as an Argument.
    Example usage:
        def cmd(name=Argument("World")):
            ...
    """
    def wrapper(func):
        _store_param_info(func, func.__name__, Argument(default, help))
        return func
    return wrapper


def OptionDecorator(default=None, help=None):
    """
    Decorator used to annotate a function parameter as an Option.
    Example usage:
        def cmd(name=Option("World", "--name")):
            ...
    """
    def wrapper(func):
        _store_param_info(func, func.__name__, Option(default, help))
        return func
    return wrapper