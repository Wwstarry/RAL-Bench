"""
Terminal UI utilities.
"""

import sys
from typing import Optional, Any


def echo(
    message: Optional[str] = None,
    file: Optional[Any] = None,
    nl: bool = True,
    err: bool = False,
    color: Optional[bool] = None,
) -> None:
    """Print a message to the terminal."""
    if file is None:
        file = sys.stderr if err else sys.stdout
    
    if message is None:
        message = ""
    
    file.write(str(message))
    if nl:
        file.write("\n")
    file.flush()


def secho(
    message: Optional[str] = None,
    file: Optional[Any] = None,
    nl: bool = True,
    err: bool = False,
    color: Optional[bool] = None,
    fg: Optional[str] = None,
    bg: Optional[str] = None,
    bold: Optional[bool] = None,
    dim: Optional[bool] = None,
    underline: Optional[bool] = None,
    blink: Optional[bool] = None,
    reverse: Optional[bool] = None,
    reset: bool = True,
) -> None:
    """Print a styled message to the terminal."""
    if message is None:
        message = ""
    
    styled = style(
        message,
        fg=fg,
        bg=bg,
        bold=bold,
        dim=dim,
        underline=underline,
        blink=blink,
        reverse=reverse,
        reset=reset,
    )
    
    echo(styled, file=file, nl=nl, err=err, color=color)


def style(
    text: str,
    fg: Optional[str] = None,
    bg: Optional[str] = None,
    bold: Optional[bool] = None,
    dim: Optional[bool] = None,
    underline: Optional[bool] = None,
    blink: Optional[bool] = None,
    reverse: Optional[bool] = None,
    reset: bool = True,
) -> str:
    """Apply ANSI styling to text."""
    # For now, just return the text as-is
    # A full implementation would add ANSI codes
    return text


def prompt(
    text: str = "",
    default: Optional[str] = None,
    hide_input: bool = False,
    type: Optional[Any] = None,
    value_proc: Optional[Any] = None,
    prompt_suffix: str = ": ",
    show_default: bool = True,
    err: bool = False,
    show_choices: bool = True,
) -> str:
    """Prompt the user for input."""
    import getpass
    
    file = sys.stderr if err else sys.stdout
    
    prompt_text = text
    if default is not None and show_default:
        prompt_text += f" [{default}]"
    prompt_text += prompt_suffix
    
    file.write(prompt_text)
    file.flush()
    
    if hide_input:
        value = getpass.getpass("")
    else:
        value = input()
    
    if not value and default is not None:
        value = default
    
    return value


def confirm(
    text: str = "",
    default: bool = False,
    abort: bool = False,
    prompt_suffix: str = " [y/N]: ",
    show_default: bool = True,
    err: bool = False,
) -> bool:
    """Prompt the user for confirmation."""
    file = sys.stderr if err else sys.stdout
    
    prompt_text = text
    if show_default:
        prompt_text += prompt_suffix
    else:
        prompt_text += ": "
    
    file.write(prompt_text)
    file.flush()
    
    value = input().lower()
    
    if value in ("y", "yes"):
        return True
    elif value in ("n", "no"):
        return False
    else:
        return default