"""
Parsing utilities for command-line arguments
"""

import shlex
from typing import Optional, List


class Statement:
    """
    Represents a parsed command statement
    """
    
    def __init__(self, command: str, args: str = '', raw: str = ''):
        """
        Initialize a Statement
        
        Args:
            command: The command name
            args: The argument string
            raw: The raw input line
        """
        self.command = command
        self.args = args
        self.raw = raw or f'{command} {args}'.strip()
        self.arg_list = self._parse_args(args)
        
    def _parse_args(self, args: str) -> List[str]:
        """Parse arguments into a list"""
        if not args:
            return []
        try:
            return shlex.split(args)
        except ValueError:
            # If shlex fails, just split on whitespace
            return args.split()
            
    def __str__(self):
        return self.raw
        
    def __repr__(self):
        return f'Statement(command={self.command!r}, args={self.args!r})'


def parse_command_line(line: str) -> Optional[Statement]:
    """
    Parse a command line into a Statement object
    
    Args:
        line: The command line to parse
        
    Returns:
        A Statement object or None if the line is empty
    """
    line = line.strip()
    if not line:
        return None
        
    parts = line.split(None, 1)
    if not parts:
        return None
        
    command = parts[0]
    args = parts[1] if len(parts) > 1 else ''
    
    return Statement(command, args, line)


class ArgumentParser:
    """
    Simple argument parser for command arguments
    """
    
    def __init__(self):
        self.arguments = []
        
    def add_argument(self, *args, **kwargs):
        """Add an argument definition"""
        self.arguments.append((args, kwargs))
        
    def parse_args(self, args):
        """Parse arguments (simplified implementation)"""
        # This is a simplified parser
        # In a full implementation, this would handle all argparse features
        class Namespace:
            pass
            
        ns = Namespace()
        
        # For now, just return an empty namespace
        # Real implementation would parse according to argument definitions
        return ns