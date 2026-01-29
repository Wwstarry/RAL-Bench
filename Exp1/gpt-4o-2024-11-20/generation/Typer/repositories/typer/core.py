import sys
from typing import Callable, List, Optional, Any, Dict

class Typer:
    def __init__(self):
        self._commands: Dict[str, Callable] = {}

    def command(self, name: Optional[str] = None):
        def decorator(func: Callable):
            command_name = name or func.__name__
            self._commands[command_name] = func
            return func
        return decorator

    def __call__(self):
        if len(sys.argv) < 2:
            self._print_help()
            sys.exit(0)

        command_name = sys.argv[1]
        if command_name in self._commands:
            func = self._commands[command_name]
            args = sys.argv[2:]
            try:
                result = func(*args)
                if isinstance(result, int):
                    sys.exit(result)
            except Exit as e:
                sys.exit(e.code)
        else:
            print(f"Error: Command '{command_name}' not found.")
            self._print_help()
            sys.exit(1)

    def _print_help(self):
        print("Usage:")
        print("  <command> [options]")
        print("\nCommands:")
        for command in self._commands:
            print(f"  {command}")

class Option:
    def __init__(self, default: Any = None):
        self.default = default

class Argument:
    def __init__(self, default: Any = None):
        self.default = default

def echo(message: str):
    print(message)

class Exit(Exception):
    def __init__(self, code: int = 0):
        self.code = code