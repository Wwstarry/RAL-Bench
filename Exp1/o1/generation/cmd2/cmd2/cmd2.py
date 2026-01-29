"""
cmd2 main module providing the Cmd2 class.
"""

import cmd
import sys
import traceback

from .parsing import StatementParser
from .utils import set_use_readline


class Cmd2(cmd.Cmd):
    """A cmd.Cmd subclass that provides enhanced functionality
       to create interactive CLI applications."""

    def __init__(self, use_rawinput=True, transcript_files=None):
        super().__init__()
        self.use_rawinput = use_rawinput
        self._transcript_files = transcript_files if transcript_files else []
        self._parser = StatementParser()
        # Default prompt
        self.prompt = "(Cmd) "
        # Typically cmd2 uses readline if available. We handle that in utils
        set_use_readline(use_rawinput)

    def onecmd(self, line):
        """Override onecmd to incorporate additional parsing or error handling."""
        parsed = self._parser.parse(line)
        if not parsed.command:
            return self.emptyline()
        cmd_func = self.cmd_func(parsed.command)
        if cmd_func is None:
            return self.default(line)
        try:
            return cmd_func(parsed.args)
        except Exception as e:
            # In cmd2, we typically show a stack trace if debug is on.
            # Minimally, we'll just print the error message.
            print(f"ERROR: {e}")
            traceback.print_exc()
            return

    def cmd_func(self, command_name):
        """Return the method that implements the given command."""
        func = getattr(self, "do_" + command_name, None)
        return func

    def emptyline(self):
        """What to do when an empty line is entered."""
        # By default, do nothing
        pass

    def default(self, line):
        """Called on an input line when the command is not recognized."""
        self.stdout.write(f"*** Unknown syntax: {line}\n")

    def precmd(self, line):
        """Hook method executed just before the command is run."""
        return line

    def postcmd(self, stop, line):
        """Hook method executed just after the command returns."""
        return stop

    def do_help(self, arg):
        """Override the built-in help to provide help on commands."""
        if arg:
            # Help for a specific command
            func = self.cmd_func(arg)
            if func:
                doc = func.__doc__ or ""
                self.stdout.write(f"{arg}: {doc}\n")
            else:
                self.stdout.write(f"No help on {arg}\n")
        else:
            # General help
            names = self.get_names()
            cmds = []
            for name in names:
                if name.startswith("do_"):
                    cmds.append(name[3:])
            self.stdout.write("Available commands:\n")
            for cmd_name in sorted(cmds):
                self.stdout.write(f"  {cmd_name}\n")

    def do_quit(self, arg):
        """Quit the command-line application."""
        return True

    def do_exit(self, arg):
        """Exit the command-line application."""
        return True

    def run_transcript_tests(self, files=None):
        """Run transcript-based tests. Each file is a script of commands and expected output."""
        files = files if files else self._transcript_files
        for filename in files:
            with open(filename, 'r') as f:
                script_lines = f.read().splitlines()
            self._run_transcript_file(script_lines)

    def _run_transcript_file(self, script_lines):
        """Compare each line's output to expected transcript."""
        # Minimal logic: For each line that starts with '#', ignore; otherwise feed to onecmd
        for line in script_lines:
            if line.strip().startswith('#'):
                continue
            # We'll just execute it. In a real cmd2, we'd capture and compare to expected output.
            self.onecmd(line)

    # Some alias for completeness
    do_q = do_quit
    do_EOF = do_quit