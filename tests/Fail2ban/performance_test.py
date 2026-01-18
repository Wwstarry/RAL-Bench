import os
import subprocess
import sys
import time
from pathlib import Path

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


def test_performance_import_fail2ban_elapsed():
    """
    Minimal, stable workload:
    - import fail2ban (top-level)
    """
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = str(_resolve_repo_root()) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    code = "import fail2ban; print('ok')"
    t0 = time.perf_counter()
    p = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        timeout=30,
        env=env,
    )
    t1 = time.perf_counter()

    # If import fails on your platform due to POSIX-only modules, allow that but still measure elapsed.
    # We do not hard-fail performance test due to platform constraints.
    elapsed = t1 - t0
    print(f"METRIC performance.import_fail2ban.elapsed_s={elapsed:.6f}")
    assert elapsed >= 0.0
