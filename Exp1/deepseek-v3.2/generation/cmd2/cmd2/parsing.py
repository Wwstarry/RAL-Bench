"""
Parsing utilities for command arguments.
"""

import shlex
from typing import List, NamedTuple, Optional


class Statement(NamedTuple):
    """
    A parsed command statement.
    
    Attributes:
        command: The command name
        args: The arguments as a string
        argv: The arguments as a list
        raw: The raw input line
    """
    command: str
    args: str
    argv: List[str]
    raw: str = ''


class ParsedString:
    """
    A string that has been parsed into tokens.
    """
    
    def __init__(self, string: str) -> None:
        """
        Initialize with a string to parse.
        
        Args:
            string: String to parse
        """
        self.raw = string
        self.tokens = shlex.split(string) if string else []
    
    def __str__(self) -> str:
        return self.raw
    
    def __repr__(self) -> str:
        return f"ParsedString(raw={self.raw!r}, tokens={self.tokens!r})"
    
    @property
    def command(self) -> Optional[str]:
        """Get the command (first token)."""
        return self.tokens[0] if self.tokens else None
    
    @property
    def args(self) -> str:
        """Get the arguments as a string."""
        return ' '.join(self.tokens[1:]) if len(self.tokens) > 1 else ''
    
    @property
    def argv(self) -> List[str]:
        """Get the arguments as a list."""
        return self.tokens
    
    def get(self, index: int, default: str = '') -> str:
        """
        Get a token by index.
        
        Args:
            index: Token index
            default: Default value if index out of range
            
        Returns:
            Token value or default
        """
        try:
            return self.tokens[index]
        except IndexError:
            return default