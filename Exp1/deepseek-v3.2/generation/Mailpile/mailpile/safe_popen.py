#!/usr/bin/env python
"""
Mailpile - Safe subprocess wrapper and pipe helpers

This module provides safe wrappers around subprocess calls with proper
error handling and resource cleanup.
"""

import os
import subprocess
import tempfile
import threading
import time
from typing import Optional, List, Union, Tuple, Any, Callable


class SafePopen(object):
    """
    Safe wrapper around subprocess.Popen with timeout support and cleanup.
    """
    
    def __init__(self, args: List[str], stdin_data: Optional[bytes] = None,
                 timeout: Optional[float] = None, **kwargs):
        """
        Initialize SafePopen.
        
        Args:
            args: Command line arguments as list
            stdin_data: Data to send to stdin (optional)
            timeout: Timeout in seconds (optional)
            **kwargs: Additional arguments passed to subprocess.Popen
        """
        self.args = args
        self.stdin_data = stdin_data
        self.timeout = timeout
        self.kwargs = kwargs
        self.process: Optional[subprocess.Popen] = None
        self.stdout: Optional[bytes] = None
        self.stderr: Optional[bytes] = None
        self.returncode: Optional[int] = None
        self._timed_out = False
        
    def run(self) -> 'SafePopen':
        """
        Execute the command and wait for completion.
        
        Returns:
            Self for chaining
        """
        try:
            # Set up stdin if we have data
            stdin_pipe = subprocess.PIPE if self.stdin_data else None
            
            # Start the process
            self.process = subprocess.Popen(
                self.args,
                stdin=stdin_pipe,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                **self.kwargs
            )
            
            # Communicate with timeout
            if self.timeout is not None:
                # Use a thread to handle communication with timeout
                def target():
                    self.stdout, self.stderr = self.process.communicate(self.stdin_data)
                
                thread = threading.Thread(target=target)
                thread.daemon = True
                thread.start()
                
                thread.join(self.timeout)
                if thread.is_alive():
                    # Timeout occurred
                    self._timed_out = True
                    self.process.terminate()
                    thread.join(5)  # Give it 5 seconds to terminate
                    if thread.is_alive():
                        self.process.kill()
                        thread.join()
                    raise subprocess.TimeoutExpired(self.args, self.timeout)
            else:
                # No timeout, just communicate
                self.stdout, self.stderr = self.process.communicate(self.stdin_data)
            
            self.returncode = self.process.returncode
            
        except Exception as e:
            # Clean up on any exception
            if self.process and self.process.poll() is None:
                self.process.terminate()
                time.sleep(0.1)
                if self.process.poll() is None:
                    self.process.kill()
            raise
            
        return self
    
    def succeeded(self) -> bool:
        """Check if the command succeeded (return code 0)."""
        return self.returncode == 0
    
    def timed_out(self) -> bool:
        """Check if the command timed out."""
        return self._timed_out
    
    def get_output(self) -> Tuple[Optional[bytes], Optional[bytes]]:
        """Get stdout and stderr as bytes."""
        return self.stdout, self.stderr
    
    def get_output_text(self, encoding: str = 'utf-8', errors: str = 'replace') -> Tuple[Optional[str], Optional[str]]:
        """Get stdout and stderr as text."""
        stdout_text = self.stdout.decode(encoding, errors) if self.stdout else None
        stderr_text = self.stderr.decode(encoding, errors) if self.stderr else None
        return stdout_text, stderr_text


def safe_popen(args: List[str], stdin_data: Optional[bytes] = None,
               timeout: Optional[float] = None, **kwargs) -> SafePopen:
    """
    Convenience function to create and run a SafePopen instance.
    
    Args:
        args: Command line arguments as list
        stdin_data: Data to send to stdin (optional)
        timeout: Timeout in seconds (optional)
        **kwargs: Additional arguments passed to subprocess.Popen
        
    Returns:
        SafePopen instance
    """
    return SafePopen(args, stdin_data, timeout, **kwargs).run()


def pipe_to_process(args: List[str], input_data: bytes, 
                    timeout: Optional[float] = None, **kwargs) -> bytes:
    """
    Pipe data to a process and return its output.
    
    Args:
        args: Command line arguments as list
        input_data: Data to send to stdin
        timeout: Timeout in seconds (optional)
        **kwargs: Additional arguments passed to subprocess.Popen
        
    Returns:
        Process stdout as bytes
        
    Raises:
        subprocess.CalledProcessError: If process returns non-zero
        subprocess.TimeoutExpired: If process times out
    """
    result = safe_popen(args, input_data, timeout, **kwargs)
    if not result.succeeded():
        raise subprocess.CalledProcessError(result.returncode, args, result.stdout, result.stderr)
    return result.stdout


def run_command(args: List[str], timeout: Optional[float] = None, 
                **kwargs) -> Tuple[int, bytes, bytes]:
    """
    Run a command and return returncode, stdout, and stderr.
    
    Args:
        args: Command line arguments as list
        timeout: Timeout in seconds (optional)
        **kwargs: Additional arguments passed to subprocess.Popen
        
    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    result = safe_popen(args, None, timeout, **kwargs)
    return result.returncode, result.stdout, result.stderr


class TemporaryPipe(object):
    """
    Context manager for creating temporary named pipes (FIFOs).
    """
    
    def __init__(self, prefix: str = "mailpile_pipe"):
        """
        Initialize TemporaryPipe.
        
        Args:
            prefix: Prefix for the pipe filename
        """
        self.prefix = prefix
        self.path: Optional[str] = None
        
    def __enter__(self) -> str:
        """Create the named pipe and return its path."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix=self.prefix + "_")
        self.path = os.path.join(temp_dir, "pipe")
        
        # Create the named pipe
        os.mkfifo(self.path)
        
        return self.path
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the named pipe and temporary directory."""
        if self.path:
            # Remove the pipe if it exists
            if os.path.exists(self.path):
                os.unlink(self.path)
            
            # Remove the parent directory
            parent_dir = os.path.dirname(self.path)
            if os.path.exists(parent_dir):
                os.rmdir(parent_dir)
            
            self.path = None


def read_pipe_with_timeout(pipe_path: str, timeout: float = 5.0) -> Optional[bytes]:
    """
    Read from a named pipe with timeout.
    
    Args:
        pipe_path: Path to the named pipe
        timeout: Timeout in seconds
        
    Returns:
        Data read from pipe, or None if timeout
    """
    start_time = time.time()
    
    # Wait for pipe to exist
    while not os.path.exists(pipe_path):
        if time.time() - start_time > timeout:
            return None
        time.sleep(0.1)
    
    # Read from pipe
    try:
        with open(pipe_path, 'rb') as pipe:
            # Set non-blocking mode
            import fcntl
            fd = pipe.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            
            # Try to read with timeout
            data = b''
            while time.time() - start_time < timeout:
                try:
                    chunk = pipe.read(4096)
                    if chunk:
                        data += chunk
                    elif data:  # No more data and we have some
                        break
                except (IOError, OSError):
                    # No data available yet
                    pass
                time.sleep(0.01)
            
            return data if data else None
            
    except Exception:
        return None