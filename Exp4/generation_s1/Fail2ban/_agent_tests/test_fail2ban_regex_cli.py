import subprocess
import sys
from pathlib import Path

def _run(args, cwd):
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

def test_fail2ban_regex_help():
    root = Path(__file__).resolve().parents[1]
    script = root / "bin" / "fail2ban-regex"
    p = _run([str(script), "--help"], cwd=root)
    assert p.returncode == 0
    assert "Offline regex tester" in p.stdout

def test_fail2ban_regex_offline_match(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = root / "bin" / "fail2ban-regex"

    log = tmp_path / "auth.log"
    log.write_text(
        "\n".join(
            [
                "noise line",
                "Failed password for root from 1.2.3.4 port 22 ssh2",
                "Failed password for root from 2001:db8::1 port 22 ssh2",
            ]
        ),
        encoding="utf-8",
    )
    regex = r"^Failed password for .* from (?P<ip>\S+) port \d+ .*$"
    p = _run([str(script), str(log), regex], cwd=root)
    assert p.returncode == 0
    assert "Matches:" in p.stdout
    assert "1.2.3.4" in p.stdout
    assert "2001:db8::1" in p.stdout

def test_fail2ban_regex_invalid_regex(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = root / "bin" / "fail2ban-regex"

    log = tmp_path / "auth.log"
    log.write_text("x\n", encoding="utf-8")

    p = _run([str(script), str(log), r"("], cwd=root)
    assert p.returncode == 2
    assert "Invalid failregex pattern" in p.stderr