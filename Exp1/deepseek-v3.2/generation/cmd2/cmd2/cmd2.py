"""
Main Cmd2 class implementation.
"""

import cmd
import sys
import argparse
import shlex
import traceback
import inspect
import functools
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    Type,
    Set,
    TextIO,
    NoReturn,
)

from .parsing import Statement, ParsedString
from .utils import CommandResult, Transcript
from .output import OutputCapturer
from .history import HistoryManager
from .decorators import (
    with_argparser,
    with_argument_list,
    with_default_category,
    with_category,
    as_subcommand_to,
    get_command_category,
    get_command_argparser,
    get_command_argument_handler,
)


class Cmd2(cmd.Cmd):
    """
    An extension of the standard library's cmd.Cmd class providing additional
    features like argument parsing, output capture, and transcript support.
    """
    
    # Class attributes that can be overridden
    prompt = '> '
    intro = None
    doc_header = 'Documented commands (type help <topic>):'
    misc_header = 'Miscellaneous help topics:'
    undoc_header = 'Undocumented commands:'
    ruler = '='
    
    # Transcript testing support
    _test_transcript: Optional[Transcript] = None
    
    def __init__(
        self,
        *args: Any,
        allow_cli_args: bool = True,
        transcript: Optional[Transcript] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Cmd2 instance.
        
        Args:
            allow_cli_args: Whether to allow command-line arguments
            transcript: Optional transcript for testing
            *args: Additional arguments passed to cmd.Cmd
            **kwargs: Additional keyword arguments passed to cmd.Cmd
        """
        super().__init__(*args, **kwargs)
        
        # Initialize output capturer
        self._output_capturer = OutputCapturer()
        
        # Initialize history manager
        self._history_manager = HistoryManager()
        
        # Set up transcript for testing
        self._test_transcript = transcript
        
        # Command registry
        self._commands: Dict[str, Callable] = {}
        self._command_categories: Dict[str, str] = {}
        self._command_help: Dict[str, str] = {}
        
        # Register all do_* methods
        self._register_commands()
        
        # Set up argument parser for command-line arguments
        if allow_cli_args:
            self._setup_argparser()
    
    def _register_commands(self) -> None:
        """Register all do_* methods as commands."""
        for attr_name in dir(self):
            if attr_name.startswith('do_'):
                command_name = attr_name[3:]
                method = getattr(self, attr_name)
                
                # Store the command
                self._commands[command_name] = method
                
                # Get command category if decorated
                category = get_command_category(method)
                if category:
                    self._command_categories[command_name] = category
                
                # Get help from docstring
                if method.__doc__:
                    self._command_help[command_name] = method.__doc__.strip()
    
    def _setup_argparser(self) -> None:
        """Set up argument parser for command-line arguments."""
        self._argparser = argparse.ArgumentParser(
            description='Cmd2 application',
            add_help=False,
        )
        self._argparser.add_argument(
            '-t', '--test',
            action='store_true',
            help='Run in test mode with transcript',
        )
        self._argparser.add_argument(
            'script',
            nargs='?',
            help='Script file to run',
        )
    
    def cmdloop(self, intro: Optional[str] = None) -> None:
        """
        Repeatedly issue a prompt, accept input, parse into a statement,
        and dispatch to action methods.
        
        Args:
            intro: Introduction message to display at start
        """
        self.preloop()
        
        # Handle test mode
        if self._test_transcript:
            return self._run_test_transcript()
        
        # Handle script file
        if hasattr(self, '_script_file'):
            return self._run_script_file()
        
        # Normal interactive mode
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro) + '\n')
            
            stop = False
            while not stop:
                try:
                    line = self._get_input()
                    if line is None:
                        # EOF
                        self.stdout.write('\n')
                        break
                    
                    # Parse and execute command
                    statement = self._parse_line(line)
                    stop = self._execute_statement(statement)
                    
                except KeyboardInterrupt:
                    self.stdout.write('\n')
                    continue
                except EOFError:
                    self.stdout.write('\n')
                    break
                except Exception as e:
                    self._handle_exception(e)
                    
        finally:
            self.postloop()
    
    def _get_input(self) -> Optional[str]:
        """Get input from user or transcript."""
        try:
            line = input(self.prompt)
            # Add to history
            self._history_manager.add(line)
            return line
        except EOFError:
            return None
    
    def _parse_line(self, line: str) -> Statement:
        """
        Parse a line of input into a Statement.
        
        Args:
            line: Input line to parse
            
        Returns:
            Parsed statement
        """
        # Split into command and arguments
        parts = shlex.split(line)
        if not parts:
            return Statement(command='', args='', argv=[])
        
        command = parts[0]
        args = ' '.join(parts[1:]) if len(parts) > 1 else ''
        
        return Statement(
            command=command,
            args=args,
            argv=parts,
            raw=line,
        )
    
    def _execute_statement(self, statement: Statement) -> bool:
        """
        Execute a parsed statement.
        
        Args:
            statement: Parsed statement to execute
            
        Returns:
            True if the command loop should stop
        """
        if not statement.command:
            return False
        
        # Check for built-in commands
        if statement.command == 'help':
            return self._do_help(statement)
        elif statement.command == 'exit':
            return True
        elif statement.command == 'quit':
            return True
        elif statement.command == 'history':
            return self._do_history(statement)
        
        # Check for registered command
        if statement.command in self._commands:
            try:
                return self._execute_command(statement)
            except SystemExit:
                # argparse sometimes calls sys.exit()
                return False
            except Exception as e:
                self._handle_exception(e)
                return False
        else:
            self.stdout.write(f"Unknown command: {statement.command}\n")
            return False
    
    def _execute_command(self, statement: Statement) -> bool:
        """
        Execute a specific command.
        
        Args:
            statement: Parsed statement
            
        Returns:
            True if the command loop should stop
        """
        command_name = statement.command
        method = self._commands[command_name]
        
        # Check for argparser decorator
        argparser = get_command_argparser(method)
        if argparser:
            try:
                parsed_args = argparser.parse_args(statement.argv[1:])
                return method(parsed_args)
            except SystemExit:
                # argparse sometimes calls sys.exit() on error
                return False
        
        # Check for argument list handler
        arg_handler = get_command_argument_handler(method)
        if arg_handler == 'args':
            return method(statement.args)
        elif arg_handler == 'argv':
            return method(statement.argv[1:])
        
        # Default: pass raw arguments string
        return method(statement.args)
    
    def _do_help(self, statement: Statement) -> bool:
        """
        Handle help command.
        
        Args:
            statement: Parsed statement
            
        Returns:
            False (doesn't stop command loop)
        """
        if statement.args:
            # Help for specific command
            command_name = statement.argv[1] if len(statement.argv) > 1 else ''
            if command_name in self._commands:
                method = self._commands[command_name]
                if method.__doc__:
                    self.stdout.write(method.__doc__.strip() + '\n')
                else:
                    self.stdout.write(f"No help for {command_name}\n")
            else:
                self.stdout.write(f"No such command: {command_name}\n")
        else:
            # General help
            self._print_help_topics()
        
        return False
    
    def _print_help_topics(self) -> None:
        """Print help topics."""
        # Group commands by category
        categorized: Dict[str, List[str]] = {}
        uncategorized: List[str] = []
        
        for cmd_name in sorted(self._commands.keys()):
            category = self._command_categories.get(cmd_name, '')
            if category:
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(cmd_name)
            else:
                uncategorized.append(cmd_name)
        
        # Print documented commands
        if self.doc_header:
            self.stdout.write(f"{self.doc_header}\n")
        
        # Print categorized commands
        for category in sorted(categorized.keys()):
            self.stdout.write(f"\n{category}:\n")
            self.stdout.write(f"{self.ruler * len(category)}\n")
            cmds = categorized[category]
            self._print_columns(cmds)
        
        # Print uncategorized commands
        if uncategorized:
            if categorized:
                self.stdout.write("\n")
            self._print_columns(uncategorized)
        
        self.stdout.write("\n")
    
    def _print_columns(self, items: List[str], width: int = 80) -> None:
        """Print items in columns."""
        if not items:
            return
        
        # Find maximum item length
        max_len = max(len(item) for item in items)
        col_width = max_len + 2
        
        # Calculate number of columns
        num_cols = max(1, width // col_width)
        num_rows = (len(items) + num_cols - 1) // num_cols
        
        # Print in columns
        for row in range(num_rows):
            line_parts = []
            for col in range(num_cols):
                idx = row + col * num_rows
                if idx < len(items):
                    item = items[idx]
                    line_parts.append(item.ljust(col_width))
            
            if line_parts:
                self.stdout.write(''.join(line_parts).rstrip() + '\n')
    
    def _do_history(self, statement: Statement) -> bool:
        """
        Handle history command.
        
        Args:
            statement: Parsed statement
            
        Returns:
            False (doesn't stop command loop)
        """
        history_items = self._history_manager.get_all()
        
        if statement.argv and len(statement.argv) > 1:
            try:
                n = int(statement.argv[1])
                history_items = history_items[-n:]
            except ValueError:
                self.stdout.write(f"Invalid number: {statement.argv[1]}\n")
                return False
        
        for i, item in enumerate(history_items, 1):
            self.stdout.write(f"{i:4d}  {item}\n")
        
        return False
    
    def _run_test_transcript(self) -> None:
        """Run commands from a test transcript."""
        if not self._test_transcript:
            return
        
        for command, expected_output in self._test_transcript.commands:
            # Execute command
            statement = self._parse_line(command)
            
            # Capture output
            with self._output_capturer.capture() as output:
                self._execute_statement(statement)
            
            # Compare with expected output
            actual_output = output.getvalue().strip()
            expected_output = expected_output.strip()
            
            if actual_output != expected_output:
                raise AssertionError(
                    f"Transcript test failed for command: {command}\n"
                    f"Expected:\n{expected_output}\n"
                    f"Actual:\n{actual_output}"
                )
    
    def _run_script_file(self) -> None:
        """Run commands from a script file."""
        # This would be implemented to read and execute commands from a file
        pass
    
    def _handle_exception(self, exc: Exception) -> None:
        """Handle an exception during command execution."""
        self.stdout.write(f"Error: {exc}\n")
        if hasattr(self, 'debug') and self.debug:
            traceback.print_exc()
    
    def default(self, line: str) -> None:
        """
        Called when input line is not recognized as a command.
        
        Args:
            line: Input line
        """
        self.stdout.write(f"Unknown command: {line.split()[0] if line else ''}\n")
    
    def emptyline(self) -> None:
        """Called when an empty line is entered."""
        pass
    
    def precmd(self, line: str) -> str:
        """
        Hook method executed just before the command line is interpreted.
        
        Args:
            line: Input line
            
        Returns:
            Modified line
        """
        return line
    
    def postcmd(self, stop: bool, line: str) -> bool:
        """
        Hook method executed just after a command dispatch is finished.
        
        Args:
            stop: Whether to stop the command loop
            line: Input line
            
        Returns:
            Whether to stop the command loop
        """
        return stop
    
    def preloop(self) -> None:
        """Hook method executed once when cmdloop() is called."""
        pass
    
    def postloop(self) -> None:
        """Hook method executed once when cmdloop() is about to return."""
        pass
    
    # Property for stdout
    @property
    def stdout(self) -> TextIO:
        """Get stdout stream."""
        return sys.stdout
    
    @stdout.setter
    def stdout(self, value: TextIO) -> None:
        """Set stdout stream."""
        # This is a no-op in this implementation
        pass
    
    # Convenience methods for output
    def poutput(self, msg: str = '', end: str = '\n') -> None:
        """
        Print output to stdout.
        
        Args:
            msg: Message to print
            end: Ending character(s)
        """
        self.stdout.write(str(msg) + end)
    
    def perror(self, msg: str = '', end: str = '\n') -> None:
        """
        Print error to stderr.
        
        Args:
            msg: Error message to print
            end: Ending character(s)
        """
        sys.stderr.write(str(msg) + end)
    
    # Transcript testing support
    @classmethod
    def test_with_transcript(cls, transcript: Transcript) -> Callable:
        """
        Decorator to run a test with a transcript.
        
        Args:
            transcript: Transcript to use for testing
            
        Returns:
            Decorator function
        """
        def decorator(test_func: Callable) -> Callable:
            @functools.wraps(test_func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Create instance with transcript
                instance = cls(transcript=transcript)
                # Run the test
                return test_func(instance, *args, **kwargs)
            return wrapper
        return decorator