"""
Utility functions for cmd2
"""

import sys
import io
from contextlib import contextmanager
from typing import TextIO, Optional


@contextmanager
def redirect_output(new_stdout: Optional[TextIO] = None, new_stderr: Optional[TextIO] = None):
    """
    Context manager to temporarily redirect stdout and/or stderr
    
    Args:
        new_stdout: New stdout stream (or None to keep current)
        new_stderr: New stderr stream (or None to keep current)
        
    Yields:
        None
    """
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    
    try:
        if new_stdout is not None:
            sys.stdout = new_stdout
        if new_stderr is not None:
            sys.stderr = new_stderr
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


class OutputCapture:
    """
    Utility class to capture output from commands
    """
    
    def __init__(self):
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        
    def __enter__(self):
        self._old_stdout = sys.stdout
        self._old_stderr = sys.stderr
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._old_stdout
        sys.stderr = self._old_stderr
        return False
        
    def get_stdout(self) -> str:
        """Get captured stdout"""
        return self.stdout.getvalue()
        
    def get_stderr(self) -> str:
        """Get captured stderr"""
        return self.stderr.getvalue()


def strip_ansi(text: str) -> str:
    """
    Remove ANSI escape sequences from text
    
    Args:
        text: Text potentially containing ANSI codes
        
    Returns:
        Text with ANSI codes removed
    """
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def align_text(text: str, width: int, align: str = 'left') -> str:
    """
    Align text within a given width
    
    Args:
        text: Text to align
        width: Width to align to
        align: Alignment type ('left', 'right', 'center')
        
    Returns:
        Aligned text
    """
    if align == 'left':
        return text.ljust(width)
    elif align == 'right':
        return text.rjust(width)
    elif align == 'center':
        return text.center(width)
    else:
        return text