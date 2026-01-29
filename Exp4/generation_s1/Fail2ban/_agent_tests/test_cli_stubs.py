import subprocess
import sys
from pathlib import Path

def test_fail2ban_client_help_no_socket():
    root = Path(__file__).resolve().parents[1]
    script = root / "bin" / "fail2ban-client"
    p = subprocess.run([sys.executable, str(script), "--help"], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert p.returncode == 0
    assert "Offline-safe subset" in p.stdout

def test_fail2ban_server_help_only():
    root = Path(__file__).resolve().parents[1]
    script = root / "bin" / "fail2ban-server"
    p = subprocess.run([sys.executable, str(script), "--help"], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert p.returncode == 0
    assert "daemon mode not implemented" in p.stdout.lower() or "not implemented" in p.stdout.lower()