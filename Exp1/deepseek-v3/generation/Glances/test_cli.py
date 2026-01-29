"""Basic CLI tests for Glances."""
import subprocess
import sys
import time


def run_glances(args):
    """Run glances with given arguments and return result."""
    cmd = [sys.executable, "-m", "glances"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def test_help():
    """Test help output."""
    returncode, stdout, stderr = run_glances(["--help"])
    assert returncode == 0
    assert "Glances" in stdout
    assert "Usage" in stdout
    print("✓ Help test passed")


def test_version():
    """Test version output."""
    returncode, stdout, stderr = run_glances(["--version"])
    assert returncode == 0
    assert "Glances" in stdout
    assert "3.4.0.1" in stdout
    print("✓ Version test passed")


def test_csv_output():
    """Test CSV output with valid fields."""
    returncode, stdout, stderr = run_glances(["--stdout-csv", "now,cpu.user,mem.used,load"])
    assert returncode == 0
    fields = stdout.strip().split(',')
    assert len(fields) == 4
    
    # Check that numeric values are parseable
    timestamp = float(fields[0])
    cpu_user = float(fields[1])
    mem_used = int(fields[2])
    load = float(fields[3])
    
    assert timestamp > 0
    assert 0 <= cpu_user <= 100
    assert mem_used >= 0
    assert load >= 0
    
    print("✓ CSV output test passed")


def test_invalid_fields():
    """Test error handling for invalid fields."""
    returncode, stdout, stderr = run_glances(["--stdout-csv", "invalid.field"])
    assert returncode != 0
    assert "Error" in stderr
    assert "Unknown field" in stderr
    print("✓ Invalid fields test passed")


def test_missing_csv_argument():
    """Test error handling for missing CSV argument."""
    returncode, stdout, stderr = run_glances(["--stdout-csv"])
    assert returncode != 0
    assert "Error" in stderr
    print("✓ Missing CSV argument test passed")


if __name__ == "__main__":
    test_help()
    test_version()
    test_csv_output()
    test_invalid_fields()
    test_missing_csv_argument()
    print("All tests passed!")