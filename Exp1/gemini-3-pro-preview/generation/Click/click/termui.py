import sys
from .utils import echo
from .exceptions import Abort

def get_current_context(silent=False):
    from .core import Context
    try:
        return Context._stack[-1]
    except IndexError:
        if not silent:
            raise RuntimeError('There is no active click context.')
        return None

def prompt(text, default=None, hide_input=False, confirmation_prompt=False, type=None, value_proc=None, prompt_suffix=': ', show_default=True, err=False):
    # Basic implementation of prompt
    if default is not None and show_default:
        text = f"{text} [{default}]"
    text += prompt_suffix
    
    echo(text, nl=False, err=err)
    
    try:
        val = input()
    except (KeyboardInterrupt, EOFError):
        raise Abort()

    if not val and default is not None:
        return default
    
    if type is not None:
        try:
            return type(val)
        except ValueError:
            echo(f"Error: invalid input", err=True)
            # In a real implementation, this would loop
            raise Abort()
            
    return val

def confirm(text, default=False, abort=False, prompt_suffix=': ', show_default=True, err=False):
    prompt_text = text
    if show_default:
        prompt_text += ' [Y/n]' if default else ' [y/N]'
    prompt_text += prompt_suffix
    
    echo(prompt_text, nl=False, err=err)
    
    try:
        val = input().lower().strip()
    except (KeyboardInterrupt, EOFError):
        raise Abort()
        
    if not val:
        ret = default
    else:
        ret = val in ('y', 'yes', '1', 'true')
        
    if abort and not ret:
        raise Abort()
    return ret