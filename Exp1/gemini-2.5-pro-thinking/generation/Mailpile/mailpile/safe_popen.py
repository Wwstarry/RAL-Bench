# mailpile.safe_popen
#
# A simplified, safer wrapper around subprocess.Popen.

import subprocess
import sys
import os

def safe_popen(command, shell=False, stdin=None, stdout=None, stderr=None):
    """
    A wrapper for subprocess.Popen that enforces safer defaults.
    """
    # On Windows, close_fds is not supported with redirected standard handles
    close_fds = sys.platform != 'win32'

    # Ensure command is a list of strings if not using shell=True
    if not shell and isinstance(command, str):
        # A simple shlex.split approximation for this benchmark
        command = command.split()

    try:
        proc = subprocess.Popen(
            command,
            shell=shell,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            close_fds=close_fds,
            # On Windows, prevent the console window from appearing
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0) if sys.platform == 'win32' else 0
        )
        return proc
    except (OSError, ValueError) as e:
        # In a real app, we'd log this error
        print(f"Failed to execute command: {command}, error: {e}")
        return None

def read_from_pipe(pipe, max_bytes=1024*1024):
    """Reads data from a process's pipe (stdout/stderr)."""
    data = b''
    if pipe:
        while len(data) < max_bytes:
            try:
                chunk = os.read(pipe.fileno(), 4096)
                if not chunk:
                    break
                data += chunk
            except (IOError, OSError):
                break
        pipe.close()
    return data

def write_to_pipe(pipe, data):
    """Writes data to a process's stdin pipe."""
    if pipe:
        try:
            pipe.write(data)
            pipe.close()
        except (IOError, OSError):
            pass # Pipe may be closed already