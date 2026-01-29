import sys
import subprocess
from mailpile.safe_popen import safe_popen, read_from_pipe

def test_safe_popen_simple_command():
    """Test running a simple command and reading its output."""
    if sys.platform == 'win32':
        command = ['cmd', '/c', 'echo', 'hello world']
    else:
        command = ['echo', 'hello world']

    proc = safe_popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc is not None
    
    stdout = read_from_pipe(proc.stdout)
    stderr = read_from_pipe(proc.stderr)
    proc.wait()

    assert proc.returncode == 0
    assert b'hello world' in stdout
    assert stderr == b''

def test_safe_popen_command_as_string():
    """Test that a string command is handled correctly."""
    if sys.platform == 'win32':
        command = 'cmd /c echo string_command'
    else:
        command = 'echo string_command'

    proc = safe_popen(command, stdout=subprocess.PIPE)
    assert proc is not None
    
    stdout = read_from_pipe(proc.stdout)
    proc.wait()

    assert b'string_command' in stdout