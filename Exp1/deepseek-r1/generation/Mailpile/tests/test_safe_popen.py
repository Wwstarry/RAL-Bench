"""Tests for mailpile.safe_popen."""
import os
import tempfile
import pytest
from mailpile.safe_popen import SafePopen

def test_safe_popen_context():
    """Test SafePopen context manager."""
    with SafePopen(['echo', 'test'], stdout=subprocess.PIPE, text=True) as proc:
        stdout, _ = proc.communicate()
        assert stdout.strip() == 'test'
        
def test_pipe_helper():
    """Test pipe helper method."""
    proc = SafePopen.pipe(['echo', 'hello'])
    stdout, _ = proc.communicate()
    assert stdout.strip() == 'hello'
    
def test_run_command():
    """Test run_command method."""
    stdout, stderr, returncode = SafePopen.run_command(['echo', 'test'])
    assert stdout.strip() == 'test'
    assert returncode == 0
    
def test_run_command_with_input():
    """Test run_command with input data."""
    stdout, stderr, returncode = SafePopen.run_command(
        ['cat'], 
        input_data='test input'
    )
    assert stdout.strip() == 'test input'
    
def test_run_command_timeout():
    """Test run_command timeout handling."""
    stdout, stderr, returncode = SafePopen.run_command(
        ['sleep', '10'],
        timeout=1
    )
    assert 'timed out' in stderr
    assert returncode == 1
    
def test_write_to_temp():
    """Test write_to_temp method."""
    content = "test content"
    temp_path = SafePopen.write_to_temp(content)
    
    try:
        with open(temp_path, 'r') as f:
            assert f.read() == content
    finally:
        os.unlink(temp_path)
        
def test_read_pipe():
    """Test read_pipe method."""
    import io
    pipe = io.StringIO("test data")
    result = SafePopen.read_pipe(pipe)
    assert result == "test data"
    
def test_read_pipe_error():
    """Test read_pipe with broken pipe."""
    import io
    class BrokenPipe:
        def read(self):
            raise IOError("Broken pipe")
            
    result = SafePopen.read_pipe(BrokenPipe())
    assert result == ""