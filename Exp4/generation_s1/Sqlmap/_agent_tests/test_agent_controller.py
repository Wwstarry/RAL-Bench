import os
import sys
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run_cli(args):
    proc = subprocess.run(
        [sys.executable, os.path.join(REPO_ROOT, "sqlmap.py"), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=10,
    )
    return proc


def test_target_provided_no_network_stub_message():
    p = run_cli(["-u", "http://example.com/?id=1"])
    assert p.returncode == 0
    assert "stub implementation" in p.stdout.lower()
    assert "target:" in p.stdout.lower()