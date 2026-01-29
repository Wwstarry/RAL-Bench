import sys
import os
import time
from mailpile.safe_popen import safe_popen

def test_echo():
    # Use Python to echo, for cross-platform
    args = [sys.executable, '-c', 'import sys; print(sys.stdin.read())']
    proc = safe_popen(args)
    out, err = proc.communicate(input=b'Hello\n')
    assert b'Hello' in out

def test_returncode():
    args = [sys.executable, '-c', 'exit(42)']
    proc = safe_popen(args)
    proc.wait()
    assert proc.returncode == 42

def test_timeout():
    args = [sys.executable, '-c', 'import time; time.sleep(2)']
    proc = safe_popen(args)
    out, err = proc.communicate(timeout=0.5)
    assert proc.returncode is not None

def test_pid():
    args = [sys.executable, '-c', 'print("PID")']
    proc = safe_popen(args)
    assert proc.pid > 0

if __name__ == '__main__':
    test_echo()
    test_returncode()
    test_timeout()
    test_pid()
    print('safe_popen tests passed')