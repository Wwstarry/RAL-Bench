"""
Minimal parsing utilities for cmd2.
"""

class ParsedStatement:
    """Simple container for a parsed command statement."""

    def __init__(self, command="", args=""):
        self.command = command
        self.args = args

class StatementParser:
    """
    Minimal statement parser to separate a command name from its arguments.
    """

    def parse(self, line):
        """Parse a line of text into a ParsedStatement of command and args."""
        line = line.strip()
        if not line:
            return ParsedStatement()
        parts = line.split(None, 1)
        if len(parts) == 1:
            return ParsedStatement(command=parts[0], args="")
        return ParsedStatement(command=parts[0], args=parts[1])