import cmd
import shlex
from typing import Any, List, Optional

from .parsing import Statement, StatementParser
from .utils.transcript import Transcript

class Cmd2(cmd.Cmd):
    """An enhanced version of cmd.Cmd with additional features."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._transcript = Transcript()
        self._statement_parser = StatementParser()
        self.prompt = "> "

    def default(self, line: str) -> Optional[bool]:
        """Called when command prefix is not recognized."""
        self.perror(f"Unknown command: {line.split()[0]}")
        return False

    def onecmd(self, line: str) -> Optional[bool]:
        """Interpret the line as a command and execute it."""
        statement = self._statement_parser.parse(line)
        self._transcript.record_command(statement.command)
        
        try:
            return super().onecmd(line)
        except Exception as e:
            self.perror(str(e))
            return False

    def precmd(self, line: str) -> str:
        """Hook method executed just before the command line is interpreted."""
        return line

    def postcmd(self, stop: bool, line: str) -> bool:
        """Hook method executed just after a command dispatch is finished."""
        return stop

    def poutput(self, msg: Any) -> None:
        """Print output to stdout."""
        print(msg)

    def perror(self, msg: Any) -> None:
        """Print error message to stderr."""
        print(f"Error: {msg}", file=sys.stderr)

    def do_help(self, arg: str) -> Optional[bool]:
        """List available commands with 'help' or detailed help with 'help cmd'."""
        if arg:
            # Detailed help for specific command
            try:
                doc = getattr(self, f'do_{arg}').__doc__
                if doc:
                    self.poutput(doc.strip())
                else:
                    self.poutput(f"No help available for '{arg}'")
            except AttributeError:
                self.poutput(f"No such command: '{arg}'")
        else:
            # List all commands
            names = self.get_names()
            commands = sorted(
                [name[3:] for name in names if name.startswith('do_')]
            )
            self.poutput("\n".join(commands))
        return False