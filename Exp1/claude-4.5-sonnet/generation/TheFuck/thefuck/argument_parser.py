"""Argument parser for TheFuck CLI."""

import sys


class Parser:
    """Simple argument parser for TheFuck."""
    
    def __init__(self):
        self.help_text = """usage: thefuck [options]

Magnificent app which corrects your previous console command.

optional arguments:
  -h, --help     show this help message and exit
  -v, --version  show program's version number and exit
  -y, --yes      confirm correction without prompting
"""
    
    def parse(self, args):
        """Parse command line arguments.
        
        Args:
            args: List of command line arguments
            
        Returns:
            Namespace object with parsed arguments
        """
        parsed = Namespace()
        parsed.help = False
        parsed.version = False
        parsed.yes = False
        parsed.command = None
        parsed.output = None
        parsed.exit_code = None
        
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg in ('-h', '--help'):
                parsed.help = True
            elif arg in ('-v', '--version'):
                parsed.version = True
            elif arg in ('-y', '--yes'):
                parsed.yes = True
            elif arg == '--command':
                if i + 1 < len(args):
                    parsed.command = args[i + 1]
                    i += 1
            elif arg == '--output':
                if i + 1 < len(args):
                    parsed.output = args[i + 1]
                    i += 1
            elif arg == '--exit-code':
                if i + 1 < len(args):
                    try:
                        parsed.exit_code = int(args[i + 1])
                    except ValueError:
                        parsed.exit_code = 1
                    i += 1
            
            i += 1
        
        return parsed
    
    def print_help(self):
        """Print help message."""
        print(self.help_text)


class Namespace:
    """Simple namespace for parsed arguments."""
    pass