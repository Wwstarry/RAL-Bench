"""
Parsing utilities for arguments and options.
"""

import shlex
from typing import List, Optional, Dict, Any


class ParsedString:
    """Represents a parsed command string with command and arguments."""
    
    def __init__(self, command: str = "", args: str = "", raw: str = ""):
        self.command = command
        self.args = args
        self.raw = raw
        self.argv = shlex.split(args) if args else []
    
    def __str__(self):
        return self.raw
    
    def __repr__(self):
        return f"ParsedString(command={self.command!r}, args={self.args!r})"


class ArgumentParser:
    """Simple argument parser for command options."""
    
    def __init__(self):
        self.options = {}
        self.arguments = []
    
    def add_option(self, short: Optional[str] = None, long: Optional[str] = None, 
                   help: str = "", action: str = "store", default: Any = None):
        """Add an option to the parser."""
        key = long or short
        self.options[key] = {
            'short': short,
            'long': long,
            'help': help,
            'action': action,
            'default': default
        }
    
    def parse(self, args: str) -> Dict[str, Any]:
        """Parse arguments."""
        try:
            argv = shlex.split(args)
        except ValueError:
            argv = args.split()
        
        result = {}
        for key, opt in self.options.items():
            result[key] = opt['default']
        
        i = 0
        while i < len(argv):
            arg = argv[i]
            found = False
            
            for key, opt in self.options.items():
                if (opt['short'] and arg == opt['short']) or \
                   (opt['long'] and arg == opt['long']):
                    if opt['action'] == 'store':
                        if i + 1 < len(argv):
                            result[key] = argv[i + 1]
                            i += 2
                        else:
                            i += 1
                    elif opt['action'] == 'store_true':
                        result[key] = True
                        i += 1
                    found = True
                    break
            
            if not found:
                i += 1
        
        return result


def parse_command_line(line: str) -> ParsedString:
    """Parse a command line into command and arguments."""
    line = line.strip()
    if not line:
        return ParsedString("", "", "")
    
    parts = line.split(None, 1)
    command = parts[0]
    args = parts[1] if len(parts) > 1 else ""
    
    return ParsedString(command=command, args=args, raw=line)


def split_args(args: str) -> List[str]:
    """Split arguments respecting quotes."""
    try:
        return shlex.split(args)
    except ValueError:
        return args.split()


def quote_arg(arg: str) -> str:
    """Quote an argument if needed."""
    if ' ' in arg or '"' in arg or "'" in arg:
        return shlex.quote(arg)
    return arg


__all__ = ["ParsedString", "ArgumentParser", "parse_command_line", "split_args", "quote_arg"]