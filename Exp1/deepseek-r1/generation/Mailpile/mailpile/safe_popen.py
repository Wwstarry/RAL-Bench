"""Safe subprocess wrapper and pipe helpers."""
import subprocess
import os
import sys
import tempfile
from typing import Optional, List, Union, IO, Any

class SafePopen:
    """Safe wrapper around subprocess.Popen with better error handling."""
    
    def __init__(self, *args, **kwargs):
        """Initialize with same arguments as subprocess.Popen."""
        self.args = args
        self.kwargs = kwargs
        self.process: Optional[subprocess.Popen] = None
        
    def __enter__(self):
        """Context manager entry."""
        self.process = subprocess.Popen(*self.args, **self.kwargs)
        return self.process
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure process is cleaned up."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
                
    @staticmethod
    def pipe(*args, **kwargs) -> subprocess.Popen:
        """Create a pipe with safe defaults."""
        kwargs.setdefault('stdin', subprocess.PIPE)
        kwargs.setdefault('stdout', subprocess.PIPE)
        kwargs.setdefault('stderr', subprocess.PIPE)
        kwargs.setdefault('text', True)
        return subprocess.Popen(*args, **kwargs)
        
    @staticmethod
    def run_command(cmd: Union[str, List[str]], 
                   input_data: Optional[str] = None,
                   timeout: Optional[int] = 30) -> tuple:
        """Run command and return (stdout, stderr, returncode)."""
        try:
            result = subprocess.run(
                cmd,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=isinstance(cmd, str)
            )
            return (result.stdout, result.stderr, result.returncode)
        except subprocess.TimeoutExpired:
            return ("", "Command timed out", 1)
        except FileNotFoundError:
            return ("", f"Command not found: {cmd}", 127)
            
    @staticmethod
    def write_to_temp(content: str, suffix: str = '.tmp') -> str:
        """Write content to temporary file and return path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            return f.name
            
    @staticmethod
    def read_pipe(pipe: IO) -> str:
        """Safely read from pipe."""
        try:
            return pipe.read()
        except (IOError, OSError):
            return ""