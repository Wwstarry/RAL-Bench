import sys
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, List, Dict, Optional, Sequence

# --- Public API Objects ---

class Exit(SystemExit):
    """
    Exit the application with a given status code.
    """
    def __init__(self, code: int = 0):
        super().__init__(code)
        self.code = code

@dataclass
class ArgumentInfo:
    """Internal representation of an Argument."""
    default: Any = ...

@dataclass
class OptionInfo:
    """Internal representation of an Option."""
    default: Any = ...
    param_decls: List[str] = field(default_factory=list)

def Argument(default: Any = ..., *, help: Optional[str] = None):
    """
    Declare a command-line argument.
    The 'help' parameter is part of the API but ignored by this implementation's help text.
    """
    return ArgumentInfo(default=default)

def Option(default: Any = ..., *param_decls: str, help: Optional[str] = None):
    """
    Declare a command-line option.
    The 'help' parameter is part of the API but ignored by this implementation's help text.
    """
    return OptionInfo(default=default, param_decls=list(param_decls))

def echo(message: Optional[str] = None, err: bool = False):
    """
    Print a message to the console (stdout or stderr).
    """
    file = sys.stderr if err else sys.stdout
    if message is None:
        message = ""
    print(message, file=file)

# --- Core Implementation ---

@dataclass
class Command:
    name: str
    callback: Callable[..., Any]
    params: Dict[str, inspect.Parameter]
    help: Optional[str] = None

class Typer:
    """
    The main Typer application class.
    """
    def __init__(self, help: Optional[str] = None):
        self._commands: Dict[str, Command] = {}
        self._prog_name: str = ""
        self._help = help

    def command(self, name: Optional[str] = None, help: Optional[str] = None) -> Callable:
        def decorator(f: Callable[..., Any]) -> Callable:
            cmd_name = name or f.__name__.lower().replace("_", "-")
            sig = inspect.signature(f)
            self._commands[cmd_name] = Command(
                name=cmd_name,
                callback=f,
                params=dict(sig.parameters),
                help=help or inspect.getdoc(f)
            )
            return f
        return decorator

    def __call__(self, args: Optional[Sequence[str]] = None, prog_name: Optional[str] = None):
        if args is None:
            args = sys.argv[1:]
        
        self._prog_name = prog_name if prog_name is not None else sys.argv[0]

        try:
            self._main(args)
        except Exit as e:
            sys.exit(e.code)
        except SystemExit as e:
            sys.exit(e.code)
        except Exception:
            # For testing, the runner will capture the traceback.
            # For real use, exit with a non-zero code.
            sys.exit(1)

    def _main(self, args: Sequence[str]):
        if not args or args[0] == "--help":
            self._print_main_help()
            raise Exit(0)

        cmd_name = args[0]
        if cmd_name not in self._commands:
            echo(f"Error: No such command '{cmd_name}'", err=True)
            raise Exit(2)

        command = self._commands[cmd_name]
        cmd_args = args[1:]

        if "--help" in cmd_args:
            self._print_command_help(command)
            raise Exit(0)

        parsed_kwargs = self._parse_args(command, cmd_args)
        command.callback(**parsed_kwargs)

    def _parse_args(self, command: Command, args: Sequence[str]) -> Dict[str, Any]:
        params = command.params
        
        positional_params_spec: List[tuple[str, inspect.Parameter]] = []
        options_spec: Dict[str, tuple[str, inspect.Parameter]] = {}
        param_values: Dict[str, Any] = {}

        for name, param in params.items():
            if isinstance(param.default, OptionInfo):
                option_info = param.default
                option_names = list(option_info.param_decls) or [f"--{name.replace('_', '-')}"]
                for opt_name in option_names:
                    options_spec[opt_name] = (name, param)
                
                if option_info.default is not ...:
                    param_values[name] = option_info.default
                elif param.annotation is bool:
                    param_values[name] = False
                else:
                    param_values[name] = None
            else:
                positional_params_spec.append((name, param))
                default_value = param.default
                if isinstance(default_value, ArgumentInfo):
                    default_value = default_value.default
                
                if default_value is not ... and default_value is not inspect.Parameter.empty:
                    param_values[name] = default_value

        arg_queue = list(args)
        positional_args_received = []

        while arg_queue:
            arg = arg_queue.pop(0)
            
            if arg.startswith('-'):
                arg_name, arg_value = (arg.split('=', 1) + [None])[:2]

                if arg_name not in options_spec:
                    echo(f"Error: No such option: {arg_name}", err=True)
                    raise Exit(2)
                
                param_name, param_spec = options_spec[arg_name]
                is_flag = param_spec.annotation is bool

                if is_flag:
                    if arg_value is not None:
                        echo(f"Error: Option '{arg_name}' does not take a value.", err=True)
                        raise Exit(2)
                    param_values[param_name] = True
                else:
                    value = arg_value
                    if value is None:
                        if not arg_queue:
                            echo(f"Error: Option '{arg_name}' requires an argument.", err=True)
                            raise Exit(2)
                        value = arg_queue.pop(0)
                    
                    if param_spec.annotation not in (inspect.Parameter.empty, Any):
                        try:
                            value = param_spec.annotation(value)
                        except (ValueError, TypeError):
                            echo(f"Error: Invalid value for {arg_name}: '{value}' is not a valid {param_spec.annotation.__name__}.", err=True)
                            raise Exit(2)
                    param_values[param_name] = value
            else:
                positional_args_received.append(arg)

        if len(positional_args_received) > len(positional_params_spec):
            extra = positional_args_received[len(positional_params_spec)]
            echo(f"Error: Got unexpected extra argument ({extra})", err=True)
            raise Exit(2)

        for i, (name, param) in enumerate(positional_params_spec):
            if i < len(positional_args_received):
                value = positional_args_received[i]
                if param.annotation not in (inspect.Parameter.empty, Any):
                    try:
                        value = param.annotation(value)
                    except (ValueError, TypeError):
                        echo(f"Error: Invalid value for argument {name.upper()}: '{value}' is not a valid {param.annotation.__name__}.", err=True)
                        raise Exit(2)
                param_values[name] = value
            elif name not in param_values:
                echo(f"Error: Missing argument '{name.upper()}'.", err=True)
                raise Exit(2)
        
        return param_values

    def _print_main_help(self):
        echo(f"Usage: {self._prog_name} [OPTIONS] COMMAND [ARGS]...")
        if self._help:
            echo(f"\n{self._help}")
        
        echo("\nOptions:")
        echo("  --help  Show this message and exit.")

        echo("\nCommands:")
        for name in sorted(self._commands.keys()):
            echo(f"  {name}")

    def _print_command_help(self, command: Command):
        usage_parts = ["Usage:", self._prog_name, command.name]
        
        options_lines = []
        arguments_lines = []

        for name, param in command.params.items():
            param_name_upper = name.upper().replace("_", "-")
            if isinstance(param.default, OptionInfo):
                option_names = list(param.default.param_decls) or [f"--{name.replace('_', '-')}"]
                usage_parts.append(f"[{option_names[0]}]")
                options_lines.append(f"  {', '.join(option_names)}")
            else:
                is_required = param.default is inspect.Parameter.empty or \
                              (isinstance(param.default, ArgumentInfo) and param.default.default is ...)
                if is_required:
                    usage_parts.append(param_name_upper)
                else:
                    usage_parts.append(f"[{param_name_upper}]")
                arguments_lines.append(f"  {param_name_upper}")

        echo(" ".join(usage_parts))
        if command.help:
            echo(f"\n{command.help.strip()}")
        
        if arguments_lines:
            echo("\nArguments:")
            for line in arguments_lines:
                echo(line)

        if options_lines:
            echo("\nOptions:")
            for line in options_lines:
                echo(line)
        
        echo("  --help  Show this message and exit.")