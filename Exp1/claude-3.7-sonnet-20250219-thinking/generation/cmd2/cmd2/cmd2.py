"""
Core implementation of cmd2 main classes.
"""

import cmd
import sys
import os
import re
import argparse
import traceback
import collections
from typing import Dict, List, Union, Optional, Any, Set, Callable, Tuple

class EmptyStatement(Exception):
    """Exception raised when an empty statement is encountered."""
    pass

class Statement:
    """Class representing a parsed command with its arguments and other metadata."""
    
    def __init__(self, command: str = '', arg_list: Optional[List[str]] = None, arg: str = '', 
                 raw: str = '', multiline_command: str = '', terminator: str = ''):
        """Initialize a Statement."""
        self.command = command
        self.arg_list = arg_list if arg_list is not None else []
        self.arg = arg
        self.raw = raw
        self.multiline_command = multiline_command
        self.terminator = terminator
        
    def __str__(self) -> str:
        """Return the raw command line used to create this Statement."""
        return self.raw

class Cmd(cmd.Cmd):
    """
    An extension of cmd.Cmd that provides additional features.
    """
    
    def __init__(self, completekey: str = 'tab', stdin=None, stdout=None, 
                 persistent_history_file: str = '', startup_script=None, use_ipython: bool = False,
                 transcript_files=None, allow_cli_args: bool = True, allow_redirection: bool = True):
        """Initialize a Cmd instance."""
        super().__init__(completekey=completekey, stdin=stdin, stdout=stdout)
        
        # Initialize attributes
        self.debug = False
        self.continuation_prompt = '> '
        self.allow_redirection = allow_redirection
        self.multiline_commands = []
        self.terminators = [';']
        self.aliases = {}
        self.settables = {}
        self.shortcuts = {}
        self.quiet = False
        
        # Output customization
        self.feedback_to_output = False
        
        # History management
        self.history = []
        self.persistent_history_file = persistent_history_file
        
        # Transcripts
        self._transcript_files = []
        if transcript_files:
            self._transcript_files = transcript_files
            
        # Initialize stderr
        self.stderr = sys.stderr
    
    def poutput(self, msg: str = '', end: str = '\n') -> None:
        """Print message to self.stdout."""
        if msg is not None:
            self.stdout.write(str(msg) + end)
            
    def perror(self, msg: str = '', end: str = '\n', apply_style: bool = True) -> None:
        """Print message to self.stderr."""
        if msg is not None:
            self.stderr.write(str(msg) + end)
            
    def pfeedback(self, msg: str = '', end: str = '\n') -> None:
        """Print feedback message."""
        if msg is not None and not self.quiet:
            if self.feedback_to_output:
                self.poutput(msg, end=end)
            else:
                self.stderr.write(str(msg) + end)
    
    def precmd(self, line: str) -> str:
        """Hook method executed just before the command is processed."""
        return line
    
    def postcmd(self, stop: bool, line: str) -> bool:
        """Hook method executed just after the command is processed."""
        return stop
    
    def parseline(self, line: str) -> Tuple[str, str, str]:
        """Parse input line into command name and arguments."""
        line = line.strip()
        if not line:
            return None, None, line
            
        i, n = 0, len(line)
        while i < n and line[i] in self.identchars:
            i += 1
        cmd, arg = line[:i], line[i:].strip()
        return cmd, arg, line
    
    def onecmd(self, line: str) -> bool:
        """Interpret the line as a command."""
        try:
            statement = self.parse(line)
            if not statement.command:
                return self.emptyline()
                
            try:
                func = getattr(self, 'do_' + statement.command)
            except AttributeError:
                return self.default(statement)
                
            return func(statement.arg)
        except EmptyStatement:
            return False
        except Exception as e:
            self.perror(f"Error: {str(e)}")
            if self.debug:
                traceback.print_exc()
            return False
    
    def parse(self, line: str) -> Statement:
        """Parse input line into a Statement object."""
        if not line.strip():
            raise EmptyStatement()
            
        command, arg, line = self.parseline(line)
        arg_list = arg.split() if arg else []
        
        # Check for shortcuts and expand
        if command in self.shortcuts:
            command = self.shortcuts[command]
            
        return Statement(command=command, arg=arg, arg_list=arg_list, raw=line)
    
    def emptyline(self) -> bool:
        """Called when an empty line is entered."""
        return False
    
    def default(self, statement: Union[Statement, str]) -> bool:
        """Called when command is not recognized."""
        if isinstance(statement, str):
            statement = self.parse(statement)
        self.perror(f"*** Unknown syntax: {statement.raw}")
        return False
    
    def completenames(self, text: str, *ignored) -> List[str]:
        """Return list of command names matching text."""
        return [cmd[3:] for cmd in self.get_names() if cmd.startswith('do_' + text)]
    
    def get_all_commands(self) -> List[str]:
        """Return a list of all command names."""
        return [cmd[3:] for cmd in self.get_names() if cmd.startswith('do_')]
    
    def get_help_topics(self) -> List[str]:
        """Return a list of help topics."""
        return [cmd[5:] for cmd in self.get_names() if cmd.startswith('help_')]
    
    def complete(self, text: str, state: int) -> Optional[str]:
        """Return the next possible completion for 'text'."""
        if state == 0:
            if text.startswith('?'):
                text = 'help ' + text[1:]
                self.completion_matches = self.completenames(text, line, 0, 0)
            else:
                line = self.readline.get_line_buffer()
                begidx = self.readline.get_begidx()
                endidx = self.readline.get_endidx()
                
                if begidx > 0:
                    cmd, args = self.parseline(line)
                    if cmd == '':
                        self.completion_matches = self.completenames(text, line, begidx, endidx)
                    else:
                        self.completion_matches = self.completedefault(text, line, begidx, endidx)
                else:
                    self.completion_matches = self.completenames(text, line, begidx, endidx)
                    
        try:
            return self.completion_matches[state]
        except IndexError:
            return None
    
    def do_help(self, arg: str) -> None:
        """List available commands with "help" or detailed help with "help cmd"."""
        if arg:
            # Check for help on a specific command
            try:
                func = getattr(self, 'help_' + arg)
                func()
            except AttributeError:
                try:
                    doc = getattr(self, 'do_' + arg).__doc__
                    if doc:
                        self.poutput(f"{arg}: {doc}")
                    else:
                        self.poutput(f"No help available for {arg}")
                except AttributeError:
                    self.poutput(f"{arg} is not a recognized command")
        else:
            # List all available commands
            cmds = self.get_all_commands()
            self.poutput("Available commands:")
            for cmd in sorted(cmds):
                self.poutput(f"  {cmd}")
                
    def cmdloop(self, intro: Optional[str] = None) -> bool:
        """Repeatedly issue a prompt, accept input, parse it, and execute the command."""
        if intro is not None:
            self.intro = intro
            
        if self.intro:
            self.poutput(str(self.intro))
            
        stop = False
        while not stop:
            try:
                line = input(self.prompt)
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            except KeyboardInterrupt:
                self.poutput()
            except Exception as e:
                self.perror(str(e))
                if self.debug:
                    traceback.print_exc()
                
        return stop