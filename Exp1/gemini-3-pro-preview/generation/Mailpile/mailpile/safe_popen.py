import subprocess
import shlex
import os
import sys

def SafePopen(cmd, **kwargs):
    """
    A wrapper around subprocess.Popen that handles argument splitting
    safely if a string is provided and shell=False.
    """
    if isinstance(cmd, str) and not kwargs.get('shell', False):
        # Split command string into list for safety unless shell=True
        if os.name == 'posix':
            cmd = shlex.split(cmd)
        else:
            # On Windows, splitting might be different, but basic split helps
            cmd = cmd.split()
            
    # Default to piping stdout/stderr if not specified, to avoid leaking to console
    if 'stdout' not in kwargs:
        kwargs['stdout'] = subprocess.PIPE
    if 'stderr' not in kwargs:
        kwargs['stderr'] = subprocess.PIPE
        
    return subprocess.Popen(cmd, **kwargs)

def PopenPipeline(cmds, stdin=None):
    """
    Chains multiple commands together in a pipeline: cmd1 | cmd2 | cmd3
    """
    prev_stdout = stdin
    procs = []
    
    for i, cmd in enumerate(cmds):
        is_last = (i == len(cmds) - 1)
        
        # For intermediate commands, pipe output. For the last one, let it return the pipe handle.
        stdout_setting = subprocess.PIPE
        
        proc = SafePopen(cmd, stdin=prev_stdout, stdout=stdout_setting)
        procs.append(proc)
        
        # Allow the previous process to receive a SIGPIPE if this one exits
        if prev_stdout:
            prev_stdout.close()
            
        prev_stdout = proc.stdout
        
    return procs[-1], procs