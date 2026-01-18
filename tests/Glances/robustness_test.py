import sys
from pathlib import Path

import pytest


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _repo_root() -> Path:
    return _project_root() / "repositories" / "glances"


def _ensure_repo_on_syspath() -> None:
    repo = _repo_root()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))


def test_001_import_core_modules() -> None:
    _ensure_repo_on_syspath()
    import glances  # noqa: F401
    from glances import globals as g  # noqa: F401


def test_002_safe_makedirs_rejects_file_collision(tmp_path: Path) -> None:
    _ensure_repo_on_syspath()
    from glances.globals import safe_makedirs

    f = tmp_path / "collision"
    f.write_text("x", encoding="utf-8")

    # If a file exists where a directory is expected, safe_makedirs should raise.
    with pytest.raises(Exception):
        safe_makedirs(str(f))


def test_003_system_exec_never_raises() -> None:
    _ensure_repo_on_syspath()
    from glances.globals import system_exec

    out = system_exec("definitely_not_a_real_command_12345")
    assert isinstance(out, str)


def test_004_to_ascii_handles_bytes_and_str() -> None:
    _ensure_repo_on_syspath()
    from glances.globals import to_ascii

    assert to_ascii("abc") == "abc"
    assert isinstance(to_ascii(b"abc"), str)
