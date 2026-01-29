import subprocess
import sys


def run_glances(args):
    return subprocess.run(
        [sys.executable, "-m", "glances", *args],
        capture_output=True,
        text=True,
    )


def test_help_ok():
    p = run_glances(["--help"])
    assert p.returncode == 0
    assert "usage" in p.stdout.lower() or "usage" in p.stderr.lower()


def test_version_ok():
    p = run_glances(["-V"])
    assert p.returncode == 0
    out = p.stdout.strip()
    assert out
    assert "glances" in out.lower()


def test_stdout_csv_basic_fields():
    p = run_glances(["--stdout-csv", "now,cpu.user,mem.used,load"])
    assert p.returncode == 0
    lines = [ln for ln in p.stdout.splitlines() if ln.strip() != ""]
    assert len(lines) == 1
    cols = lines[0].split(",")
    assert len(cols) == 4

    # cpu.user, mem.used, load must be numeric parseable
    float(cols[1])
    float(cols[2])
    float(cols[3])


def test_stdout_csv_missing_arg_nonzero():
    p = run_glances(["--stdout-csv"])
    assert p.returncode != 0
    assert (p.stderr.strip() or p.stdout.strip())


def test_unknown_field_nonzero_and_message():
    p = run_glances(["--stdout-csv", "now,wat"])
    assert p.returncode != 0
    assert p.stderr.strip() != ""
    assert p.stdout.strip() == ""