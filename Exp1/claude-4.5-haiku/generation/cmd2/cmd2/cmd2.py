"""
Core Cmd2 class implementation.
"""

import cmd
import sys
import os
import re
import shlex
import traceback
from typing import Optional, List, Dict, Any, Callable, Tuple
from io import StringIO
from pathlib import Path

from . import parsing
from . import utils


class Cmd2(cmd.Cmd):
    """
    A pure Python interactive command-line application framework.
    Subclasses cmd.Cmd and provides enhanced functionality.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transcript_file = None
        self.transcript_lines = []
        self.last_result = None
        self.last_output = ""
        self._output_capture = None
        self._capture_output = False
        self._command_history = []
        self.abbrev = True
        self.debug = False
        self.echo = False
        self.timing = False
        self.exit_code = 0
        self._locals = {}
    
    def onecmd(self, line: str) -> bool:
        """
        Execute a single command.
        Returns True if the command should exit the application.
        """
        if not line:
            return False
        
        # Record in history
        self._command_history.append(line)
        
        # Parse the command
        parsed = parsing.parse_command_line(line)
        
        if not parsed.command:
            return False
        
        # Handle help
        if parsed.command == "help":
            return self.onecmd_help(parsed.args)
        
        # Look for do_<command> method
        method_name = f"do_{parsed.command}"
        
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            try:
                # Capture output if needed
                if self._capture_output:
                    old_stdout = sys.stdout
                    sys.stdout = StringIO()
                
                result = method(parsed.args)
                
                if self._capture_output:
                    self.last_output = sys.stdout.getvalue()
                    sys.stdout = old_stdout
                
                self.last_result = result
                return result if isinstance(result, bool) else False
            except Exception as e:
                if self._capture_output:
                    sys.stdout = old_stdout
                self.last_output = ""
                self.poutput(f"Error: {e}")
                if self.debug:
                    traceback.print_exc()
                return False
        else:
            self.poutput(f"Unknown command: {parsed.command}")
            return False
    
    def onecmd_help(self, args: str) -> bool:
        """Handle help command."""
        if args:
            # Help for specific command
            method_name = f"do_{args}"
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                if method.__doc__:
                    self.poutput(method.__doc__)
                else:
                    self.poutput(f"No help available for {args}")
            else:
                self.poutput(f"Unknown command: {args}")
        else:
            # List all commands
            self.poutput("Available commands:")
            for attr in dir(self):
                if attr.startswith("do_") and attr != "do_help":
                    cmd_name = attr[3:]
                    method = getattr(self, attr)
                    doc = method.__doc__ or ""
                    first_line = doc.split("\n")[0] if doc else ""
                    self.poutput(f"  {cmd_name:15} {first_line}")
        return False
    
    def poutput(self, msg: str = "", end: str = "\n") -> None:
        """Print output to stdout."""
        if msg or end:
            print(msg, end=end)
    
    def perror(self, msg: str = "", end: str = "\n", apply_style: bool = True) -> None:
        """Print error output to stderr."""
        if msg or end:
            print(msg, file=sys.stderr, end=end)
    
    def pfeedback(self, msg: str) -> None:
        """Print feedback message."""
        self.poutput(msg)
    
    def cmdloop(self, intro: Optional[str] = None) -> None:
        """
        Run the command loop.
        """
        if intro:
            self.poutput(intro)
        
        try:
            super().cmdloop(intro="")
        except KeyboardInterrupt:
            self.poutput("\nInterrupted")
        except EOFError:
            self.poutput("")
    
    def emptyline(self) -> bool:
        """Handle empty line input."""
        return False
    
    def default(self, line: str) -> bool:
        """Handle unknown command."""
        self.poutput(f"Unknown command: {line}")
        return False
    
    def get_all_commands(self) -> List[str]:
        """Get list of all available commands."""
        commands = []
        for attr in dir(self):
            if attr.startswith("do_") and attr != "do_help":
                commands.append(attr[3:])
        return sorted(commands)
    
    def get_command_help(self, command: str) -> str:
        """Get help text for a command."""
        method_name = f"do_{command}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method.__doc__ or f"Help for {command}"
        return ""
    
    def complete_command(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """Provide tab completion for commands."""
        commands = self.get_all_commands()
        if text:
            return [cmd for cmd in commands if cmd.startswith(text)]
        return commands
    
    def parseline(self, line: str) -> Tuple[str, str, str]:
        """Parse a line into command, args, and raw line."""
        line = line.strip()
        if not line:
            return "", "", line
        
        parts = line.split(None, 1)
        command = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        
        return command, args, line
    
    def run_script(self, script_path: str) -> None:
        """Run commands from a script file."""
        try:
            with open(script_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.onecmd(line)
        except FileNotFoundError:
            self.perror(f"Script file not found: {script_path}")
    
    def capture_output(self, func: Callable, *args, **kwargs) -> Tuple[str, Any]:
        """Capture output from a function call."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            result = func(*args, **kwargs)
            output = sys.stdout.getvalue()
            return output, result
        finally:
            sys.stdout = old_stdout
    
    def start_transcript(self, filename: str) -> None:
        """Start recording transcript to file."""
        self.transcript_file = filename
        self.transcript_lines = []
    
    def stop_transcript(self) -> None:
        """Stop recording transcript and write to file."""
        if self.transcript_file:
            with open(self.transcript_file, 'w') as f:
                f.write('\n'.join(self.transcript_lines))
            self.transcript_file = None
            self.transcript_lines = []
    
    def add_transcript_line(self, line: str) -> None:
        """Add a line to the transcript."""
        if self.transcript_file:
            self.transcript_lines.append(line)


__all__ = ["Cmd2"]