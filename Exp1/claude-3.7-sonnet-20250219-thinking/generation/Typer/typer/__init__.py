from typer.main import Typer
from typer.params import Option, Argument
from typer.testing import CliRunner

__version__ = "0.1.0"

def echo(message, nl=True, err=False, color=None):
    """Print a message to stdout or stderr."""
    if err:
        import sys
        file = sys.stderr
    else:
        import sys
        file = sys.stdout
    
    if nl:
        print(message, file=file)
    else:
        print(message, end="", file=file)

class Exit(Exception):
    """Exception that signals to exit the CLI application with a specific exit code."""
    def __init__(self, code=0):
        self.code = code
        super().__init__(f"Exit with status code: {code}")

__all__ = ["Typer", "Option", "Argument", "echo", "Exit", "CliRunner"]