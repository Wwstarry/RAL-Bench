import subprocess
import sys

def run_glances(args):
    cmd = [sys.executable, "-m", "glances"] + args
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def test_help():
    result = run_glances(["--help"])
    assert result.returncode == 0
    assert "usage:" in result.stdout

def test_version():
    result = run_glances(["--version"])
    assert result.returncode == 0
    assert "glances" in result.stdout

def test_stdout_csv_now():
    result = run_glances(["--stdout-csv", "now"])
    assert result.returncode == 0
    val = float(result.stdout.strip())
    assert val > 0

def test_stdout_csv_cpu_user_mem_used_load():
    result = run_glances(["--stdout-csv", "now,cpu.user,mem.used,load"])
    assert result.returncode == 0
    parts = result.stdout.strip().split(",")
    assert len(parts) == 4
    float(parts[0])  # now
    float(parts[1])  # cpu.user
    float(parts[2])  # mem.used
    float(parts[3])  # load

def test_stdout_csv_unknown_field():
    result = run_glances(["--stdout-csv", "now,foo"])
    assert result.returncode != 0
    assert "unknown field" in result.stderr

def test_missing_stdout_csv_arg():
    result = run_glances([])
    assert result.returncode != 0
    assert "missing required argument" in result.stderr