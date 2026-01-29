"""
Utility functions for cmd2.
"""

import sys

def strip_quotes(s):
    """Remove surrounding quotes from a string if present."""
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s

def quote_string(s):
    """Add surrounding quotes to a string if not already present."""
    if not (s.startswith('"') and s.endswith('"')) and not (s.startswith("'") and s.endswith("'")):
        return f"'{s}'"
    return s

def wrap_text(text, width=70):
    """Wrap text to the specified width."""
    lines = []
    current_line = ""
    for word in text.split():
        if len(current_line) + len(word) + 1 > width:
            lines.append(current_line)
            current_line = word
        else:
            if current_line:
                current_line += " "
            current_line += word
    if current_line:
        lines.append(current_line)
    return "\n".join(lines)

def set_use_readline(use_rawinput):
    """Placeholder function to handle any readline setup if necessary."""
    if use_rawinput:
        try:
            import readline  # noqa
        except ImportError:
            pass