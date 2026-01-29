"""Tests for mailpile.safe_popen module."""

import pytest
import subprocess
from mailpile.safe_popen import SafePopen, safe_popen, pipe_data


class TestSafePopen:
    """Test SafePopen class."""
    
    def test_simple_command(self):
        """Test executing a simple command."""
        with SafePopen(['echo', 'hello'], stdout=subprocess.PIPE) as proc:
            stdout, stderr = proc.communicate()
        assert b'hello' in stdout
    
    def test_command_with_input(self):
        """Test piping input to a command."""
        with SafePopen(['cat'], stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE) as proc:
            stdout, stderr = proc.communicate(input=b'test data')
        assert stdout == b'test data'
    
    def test_command_failure(self):
        """Test handling command failure."""
        with SafePopen(['false'], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE) as proc:
            returncode = proc.wait()
        assert returncode != 0
    
    def test_poll(self):
        """Test polling process status."""
        with SafePopen(['sleep', '0.1'], stdout=subprocess.PIPE) as proc:
            assert proc.poll() is None or proc.poll() == 0
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with SafePopen(['echo', 'test'], stdout=subprocess.PIPE) as proc:
            assert proc.process is not None
        # Process should be cleaned up after context exit
    
    def test_invalid_command(self):
        """Test handling of invalid command."""
        with pytest.raises(RuntimeError):
            SafePopen(['nonexistent_command_xyz'], shell=False)


class TestSafePopenFunction:
    """Test safe_popen function."""
    
    def test_safe_popen_basic(self):
        """Test basic safe_popen usage."""
        proc = safe_popen(['echo', 'hello'], timeout=5)
        stdout, stderr = proc.communicate()
        assert b'hello' in stdout
    
    def test_safe_popen_with_timeout(self):
        """Test safe_popen with timeout."""
        proc = safe_popen(['echo', 'test'], timeout=10)
        stdout, stderr = proc.communicate()
        assert stdout == b'test\n'


class TestPipeData:
    """Test pipe_data function."""
    
    def test_pipe_data_basic(self):
        """Test basic data piping."""
        stdout, stderr, returncode = pipe_data(b'hello world', ['cat'])
        assert stdout == b'hello world'
        assert returncode == 0
    
    def test_pipe_data_with_processing(self):
        """Test piping data through a processing command."""
        stdout, stderr, returncode = pipe_data(b'HELLO', ['tr', 'A-Z', 'a-z'])
        assert stdout == b'hello'
        assert returncode == 0
    
    def test_pipe_data_empty_input(self):
        """Test piping empty data."""
        stdout, stderr, returncode = pipe_data(b'', ['cat'])
        assert stdout == b''
        assert returncode == 0