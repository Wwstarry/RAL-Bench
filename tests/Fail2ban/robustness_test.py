import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

TARGET_ENV = "FAIL2BAN_TARGET"
TARGET_REFERENCE_VALUE = "reference"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_repo_root() -> Path:
    root = _project_root()
    target = os.getenv(TARGET_ENV, TARGET_REFERENCE_VALUE)
    if target == TARGET_REFERENCE_VALUE:
        rr = os.getenv("RACB_REPO_ROOT")
        repo = Path(rr).resolve() if rr else (root / "repositories" / "fail2ban").resolve()
    else:
        repo = (root / "generation" / "Fail2ban").resolve()
    if (repo / "src" / "fail2ban").is_dir():
        return (repo / "src").resolve()
    return repo


def _run(script: Path, args, timeout_s: int = 25) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = str(_resolve_repo_root()) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return subprocess.run(
        [sys.executable, str(script), *list(args)],
        text=True,
        input="",
        capture_output=True,
        timeout=timeout_s,
        env=env,
    )


def _out(p: subprocess.CompletedProcess) -> str:
    return (p.stdout + "\n" + p.stderr).lower()


def test_001_fail2ban_regex_missing_log_file_fails_fast():
    base = _resolve_repo_root()
    script = base / "bin" / "fail2ban-regex"
    p = _run(script, ["this_file_should_not_exist.log", "Failed password"], timeout_s=20)
    out = _out(p)
    assert ("no such file" in out) or ("not found" in out) or ("error" in out) or ("unable" in out)


def test_002_fail2ban_regex_invalid_regex_reports_error():
    base = _resolve_repo_root()
    script = base / "bin" / "fail2ban-regex"

    with tempfile.TemporaryDirectory(prefix="racb_fail2ban_") as td:
        logp = Path(td) / "x.log"
        logp.write_text("Failed password for invalid user root from 203.0.113.5\n", encoding="utf-8")

        # invalid regex: unbalanced bracket
        p = _run(script, [str(logp), r"(unbalanced["], timeout_s=20)
        out = _out(p)
        assert ("error" in out) or ("exception" in out) or ("re.error" in out) or ("invalid" in out)


def test_003_fail2ban_client_unknown_command_reports_usage():
    base = _resolve_repo_root()
    script = base / "bin" / "fail2ban-client"
    p = _run(script, ["this-command-should-not-exist"], timeout_s=20)
    out = _out(p)
    assert ("usage" in out) or ("unknown" in out) or ("error" in out)


def test_004_fail2ban_client_help_does_not_hang():
    base = _resolve_repo_root()
    script = base / "bin" / "fail2ban-client"
    p = _run(script, ["-h"], timeout_s=20)
    out = _out(p)
    assert ("usage" in out) or ("options" in out) or ("fail2ban-client" in out)


def test_005_fail2ban_regex_help_does_not_hang():
    base = _resolve_repo_root()
    script = base / "bin" / "fail2ban-regex"
    p = _run(script, ["-h"], timeout_s=20)
    out = _out(p)
    assert ("usage" in out) or ("options" in out) or ("fail2ban-regex" in out)
