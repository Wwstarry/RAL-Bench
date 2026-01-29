"""
Utility functions for cmd2.
"""

from typing import Any, Optional, List
import sys
import os


def safe_str(obj: Any) -> str:
    """Safely convert object to string."""
    try:
        return str(obj)
    except Exception:
        return repr(obj)


def strip_ansi(text: str) -> str:
    """Remove ANSI color codes from text."""
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def align_text(text: str, width: int = 80, indent: int = 0) -> str:
    """Align text to specified width."""
    lines = text.split('\n')
    result = []
    prefix = ' ' * indent
    for line in lines:
        if len(line) > width:
            result.append(prefix + line[:width])
        else:
            result.append(prefix + line)
    return '\n'.join(result)


def get_terminal_width() -> int:
    """Get terminal width."""
    try:
        return os.get_terminal_size().columns
    except (AttributeError, ValueError, OSError):
        return 80


def get_terminal_height() -> int:
    """Get terminal height."""
    try:
        return os.get_terminal_size().lines
    except (AttributeError, ValueError, OSError):
        return 24


def format_table(rows: List[List[str]], headers: Optional[List[str]] = None) -> str:
    """Format data as a table."""
    if not rows:
        return ""
    
    # Calculate column widths
    num_cols = len(rows[0]) if rows else 0
    col_widths = [0] * num_cols
    
    if headers:
        for i, header in enumerate(headers):
            col_widths[i] = max(col_widths[i], len(str(header)))
    
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Build table
    lines = []
    
    if headers:
        header_line = " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
        lines.append(header_line)
        lines.append("-" * len(header_line))
    
    for row in rows:
        row_line = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
        lines.append(row_line)
    
    return "\n".join(lines)


class OutputCapture:
    """Context manager for capturing output."""
    
    def __init__(self):
        self.output = ""
        self.old_stdout = None
        self.old_stderr = None
    
    def __enter__(self):
        from io import StringIO
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.output = sys.stdout.getvalue()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        return False
    
    def get_output(self) -> str:
        """Get captured output."""
        return self.output


__all__ = [
    "safe_str",
    "strip_ansi",
    "align_text",
    "get_terminal_width",
    "get_terminal_height",
    "format_table",
    "OutputCapture",
]