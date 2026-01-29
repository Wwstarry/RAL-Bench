"""Utility functions for TheFuck."""

import os
import subprocess
from thefuck.types import Command


def get_previous_command(args):
    """Get the previous command from arguments or history.
    
    Args:
        args: Parsed arguments namespace
        
    Returns:
        Command object or None
    """
    # If command is provided via arguments, use it
    if hasattr(args, 'command') and args.command:
        output = getattr(args, 'output', '')
        exit_code = getattr(args, 'exit_code', 1)
        return Command(args.command, output=output, exit_code=exit_code)
    
    # Try to get from environment variables (set by shell integration)
    script = os.environ.get('TF_CMD')
    if script:
        output = os.environ.get('TF_CMD_OUTPUT', '')
        exit_code = int(os.environ.get('TF_CMD_EXIT_CODE', '1'))
        return Command(script, output=output, exit_code=exit_code)
    
    return None


def which(program):
    """Find executable in PATH.
    
    Args:
        program: Program name to find
        
    Returns:
        Full path to program or None
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ.get("PATH", "").split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    
    return None