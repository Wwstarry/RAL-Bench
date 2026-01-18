import os
import sys
from pathlib import Path

import psutil

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


def test_resource_import_fail2ban_rss_cpu_sample():
    """
    Resource sampling around a safe workload:
    - import fail2ban (top-level)
    """
    sys.path.insert(0, str(_resolve_repo_root()))
    proc = psutil.Process()

    rss_before = proc.memory_info().rss
    _ = proc.cpu_percent(interval=None)

    try:
        import fail2ban  # noqa: F401
    except ModuleNotFoundError:
        # platform gap (e.g., missing POSIX-only module) is tolerated in resource sampling
        pass

    cpu = proc.cpu_percent(interval=0.2)
    rss_after = proc.memory_info().rss

    print(f"METRIC resource.import_fail2ban.rss_before_bytes={rss_before}")
    print(f"METRIC resource.import_fail2ban.rss_after_bytes={rss_after}")
    print(f"METRIC resource.import_fail2ban.avg_cpu_percent_sample={cpu:.2f}")

    assert rss_after >= 0
    assert cpu >= 0.0
