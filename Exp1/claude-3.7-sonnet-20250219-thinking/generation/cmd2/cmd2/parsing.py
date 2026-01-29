"""
Parsing utilities for cmd2.
"""

import argparse
import functools
from typing import Dict, List, Union, Optional, Any, Set, Callable, Tuple

def with_argparser(parser: argparse.ArgumentParser, ns_provider: Optional[Callable] = None,
                 preserve_quotes: bool = False) -> Callable:
    """
    Decorator for command functions to use argparse for argument parsing.
    
    Parameters:
        parser (argparse.ArgumentParser): ArgumentParser instance to use
        ns_provider (Optional[Callable]): Callable that returns an argparse Namespace
        preserve_quotes (bool): If True, preserve quotes in arguments
        
    Returns:
        Callable: Wrapped function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(instance, args):
            try:
                if isinstance(args, str):
                    # Split the string into an arg list
                    arg_list = args.split()
                else:
                    arg_list = args
                
                if ns_provider:
                    namespace = ns_provider()
                    parsed_args = parser.parse_args(arg_list, namespace)
                else:
                    parsed_args = parser.parse_args(arg_list)
                return func(instance, parsed_args)
            except SystemExit:
                return False
            except Exception as e:
                instance.perror(str(e))
                return False
        
        # Store parser in the function for help generation
        wrapper.__argparser__ = parser
        return wrapper
    
    return decorator

def with_argument_list(preserve_quotes: bool = False) -> Callable:
    """
    Decorator that passes args as a list instead of a string.
    
    Parameters:
        preserve_quotes (bool): If True, preserve quotes in arguments
        
    Returns:
        Callable: Wrapped function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(instance, args):
            if isinstance(args, str):
                # Split the string into an arg list
                args = args.split()
            return func(instance, args)
        return wrapper
    return decorator

def parse_quoted_string(cmdline: str) -> List[str]:
    """Parse a command line respecting quotes."""
    import shlex
    return shlex.split(cmdline)