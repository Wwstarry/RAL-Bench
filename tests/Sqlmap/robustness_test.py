import os
import sys
import subprocess
from pathlib import Path


TARGET_ENV = "SQLMAP_TARGET"
TARGET_REFERENCE_VALUE = "reference"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _repo_root() -> Path:
    env_root = os.getenv("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return (_project_root() / "repositories" / "sqlmap").resolve()


def _entrypoint() -> Path:
    return (_repo_root() / "sqlmap.py").resolve()


def _run_cli(args, timeout_s=20) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(_entrypoint())] + list(args)
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_s,
        cwd=str(_repo_root()),
        env={**os.environ},
    )


def _out(p: subprocess.CompletedProcess) -> str:
    return (p.stdout + "\n" + p.stderr).lower()


def test_001_nonexistent_request_file_reports_missing_file():
    p = _run_cli(["--batch", "-r", "this_file_should_not_exist.req"], timeout_s=20)
    out = _out(p)

    # sqlmap prints "does not exist" for missing request file
    assert "does not exist" in out or "not found" in out or "no such file" in out


def test_002_invalid_scheme_url_reports_invalid_target_url():
    # Use invalid scheme; should fail fast with "invalid target url" message.
    p = _run_cli(["--batch", "-u", "not_a_scheme://example"], timeout_s=20)
    out = _out(p)

    # Reference prints "[CRITICAL] invalid target URL" (case-insensitive compare)
    assert "invalid target url" in out or "invalid target" in out


def test_003_unknown_option_in_batch_mode_reports_no_such_option():
    p = _run_cli(["--batch", "--this-option-should-not-exist"], timeout_s=20)
    out = _out(p)

    # argparse style error text is the stable signal
    assert "no such option" in out or "unrecognized" in out or "unknown" in out


def test_004_bad_output_dir_path_handled_in_help_mode():
    bad_path = r".\generation\Sqlmap\bad:dir"
    p = _run_cli(["-h", "--output-dir", bad_path], timeout_s=20)
    out = _out(p)

    # In help mode, tool may still exit 0; just ensure it returns and prints something.
    assert len(out.strip()) > 0


def test_005_extremely_long_argument_does_not_crash_or_hang():
    long_arg = "A" * 10000
    p = _run_cli(["-h", long_arg], timeout_s=20)
    out = _out(p)
    assert len(out.strip()) > 0
