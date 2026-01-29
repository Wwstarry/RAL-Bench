import subprocess
import os

def safe_popen(command, stdin=None, stdout=None, stderr=None, shell=False):
    """
    A safe wrapper around subprocess.Popen to handle common edge cases.
    """
    try:
        process = subprocess.Popen(
            command,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            shell=shell,
            close_fds=True
        )
        return process
    except Exception as e:
        raise RuntimeError(f"Failed to execute command {command}: {e}")

def pipe_output(process):
    """
    Helper to read output from a subprocess.
    """
    try:
        stdout, stderr = process.communicate()
        return stdout, stderr
    except Exception as e:
        raise RuntimeError(f"Failed to read process output: {e}")