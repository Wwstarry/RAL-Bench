"""Safe subprocess wrapper and pipe helpers."""

import subprocess
import os
import signal
from typing import Optional, List, Tuple, Union


class SafePopen:
    """Safe wrapper around subprocess.Popen with resource management."""
    
    def __init__(self, args: Union[str, List[str]], shell: bool = False,
                 stdin=None, stdout=None, stderr=None, timeout: Optional[float] = None):
        """
        Initialize SafePopen.
        
        Args:
            args: Command to execute (string or list)
            shell: Whether to use shell execution
            stdin: stdin file descriptor
            stdout: stdout file descriptor
            stderr: stderr file descriptor
            timeout: Timeout in seconds
        """
        self.args = args
        self.shell = shell
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.timeout = timeout
        self.process = None
        self._start()
    
    def _start(self):
        """Start the subprocess."""
        try:
            self.process = subprocess.Popen(
                self.args,
                shell=self.shell,
                stdin=self.stdin,
                stdout=self.stdout,
                stderr=self.stderr,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start process: {e}")
    
    def communicate(self, input: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Communicate with the process.
        
        Args:
            input: Input data to send to stdin
            
        Returns:
            Tuple of (stdout, stderr)
        """
        try:
            stdout, stderr = self.process.communicate(input=input, timeout=self.timeout)
            return stdout or b'', stderr or b''
        except subprocess.TimeoutExpired:
            self.kill()
            raise
    
    def kill(self):
        """Kill the process and its children."""
        if self.process and self.process.poll() is None:
            try:
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    self.process.terminate()
            except (OSError, ProcessLookupError):
                pass
    
    def wait(self) -> int:
        """Wait for process to complete and return exit code."""
        if self.process:
            return self.process.wait(timeout=self.timeout)
        return -1
    
    def poll(self) -> Optional[int]:
        """Check if process has completed."""
        if self.process:
            return self.process.poll()
        return None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.kill()
        return False


def safe_popen(cmd: Union[str, List[str]], shell: bool = False,
               timeout: Optional[float] = None) -> SafePopen:
    """
    Create a safe subprocess.
    
    Args:
        cmd: Command to execute
        shell: Whether to use shell
        timeout: Timeout in seconds
        
    Returns:
        SafePopen instance
    """
    return SafePopen(cmd, shell=shell, timeout=timeout)


def pipe_data(data: bytes, cmd: Union[str, List[str]],
              shell: bool = False) -> Tuple[bytes, bytes, int]:
    """
    Pipe data through a command.
    
    Args:
        data: Input data
        cmd: Command to execute
        shell: Whether to use shell
        
    Returns:
        Tuple of (stdout, stderr, returncode)
    """
    with SafePopen(cmd, shell=shell, stdin=subprocess.PIPE,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        stdout, stderr = proc.communicate(input=data)
        returncode = proc.wait()
    return stdout, stderr, returncode