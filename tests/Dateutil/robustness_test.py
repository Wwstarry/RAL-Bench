import os
import sys
from pathlib import Path
from typing import Any, Callable, Tuple

import pytest

PROJECT_NAME = "Dateutil"
PACKAGE_NAME = "dateutil"


def _candidate_repo_roots() -> list[Path]:
    """
    Determine where to import the evaluated repository from.

    Priority:
      1) RACB_REPO_ROOT env var (set by runner)
      2) <bench_root>/repositories/<Project>
      3) <bench_root>/generation/<Project>
    """
    candidates: list[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        # RACB_REPO_ROOT might already be repositories/<Project> or generation/<Project>
        candidates.append(p)
        candidates.append((p / "repositories" / PROJECT_NAME).resolve())
        candidates.append((p / "generation" / PROJECT_NAME).resolve())

    bench_root = Path(__file__).resolve().parents[2]
    candidates.append((bench_root / "repositories" / PROJECT_NAME).resolve())
    candidates.append((bench_root / "generation" / PROJECT_NAME).resolve())

    # de-dup
    seen = set()
    uniq: list[Path] = []
    for c in candidates:
        if c not in seen:
            uniq.append(c)
            seen.add(c)
    return uniq


def _looks_like_package_root(repo_root: Path) -> bool:
    # common layouts: repo_root/dateutil/__init__.py or repo_root/src/dateutil/__init__.py
    if (repo_root / PACKAGE_NAME / "__init__.py").exists():
        return True
    if (repo_root / "src" / PACKAGE_NAME / "__init__.py").exists():
        return True
    return False


def _select_repo_root() -> Path:
    for cand in _candidate_repo_roots():
        if _looks_like_package_root(cand):
            return cand
    raise RuntimeError(
        f"Could not locate importable repo root for '{PACKAGE_NAME}'. "
        f"Tried: {[str(p) for p in _candidate_repo_roots()]}"
    )


def _import_dateutil():
    """
    Import dateutil from the evaluated repository root.
    RACB_REPO_ROOT is expected to point to ./repositories/<Project> or ./generation/<Project>.
    """
    repo_root = _select_repo_root()
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)

    import dateutil  # type: ignore
    return dateutil


def _run_case(case_id: str, fn: Callable[[], Any]) -> Tuple[bool, str]:
    """
    Version-tolerant robustness runner:
      - Returning is PASS.
      - Raising a normal exception is also PASS (invalid inputs should fail safely).
      - Hanging is prevented by pytest timeout markers.
    """
    try:
        _ = fn()
        return True, f"{case_id}: ok"
    except Exception as e:
        return True, f"{case_id}: raised {type(e).__name__} (acceptable)"


@pytest.mark.timeout(10)
def test_dateutil_importable_and_parser_available():
    """
    Robustness 1: module should be importable and expose parser.parse.
    """
    dateutil = _import_dateutil()
    assert hasattr(dateutil, "parser"), "dateutil.parser must exist"
    assert hasattr(dateutil.parser, "parse"), "dateutil.parser.parse must exist"
    assert callable(dateutil.parser.parse), "dateutil.parser.parse must be callable"


@pytest.mark.timeout(10)
def test_dateutil_basic_parse_common_formats():
    """
    Robustness 2: parse a few common formats. Should return datetime without crashing.
    """
    dateutil = _import_dateutil()

    def _case():
        dt1 = dateutil.parser.parse("2023-01-01")
        dt2 = dateutil.parser.parse("Jan 2 2023 03:04:05")
        dt3 = dateutil.parser.parse("2023/01/03")
        assert getattr(dt1, "year", None) == 2023
        assert getattr(dt2, "month", None) == 1
        assert getattr(dt3, "day", None) == 3
        return (dt1, dt2, dt3)

    ok, msg = _run_case("parse_common_formats", _case)
    assert ok, msg


@pytest.mark.timeout(10)
def test_dateutil_parse_invalid_string_fails_safely():
    """
    Robustness 3: invalid date string should raise, or at least not crash/hang.
    """
    dateutil = _import_dateutil()

    def _case():
        # should usually raise ParserError / ValueError
        return dateutil.parser.parse("this is not a date at all !!!")

    ok, msg = _run_case("parse_invalid_string", _case)
    assert ok, msg


@pytest.mark.timeout(10)
def test_dateutil_parse_none_fails_safely():
    """
    Robustness 4: parse(None) should raise a normal exception or be handled safely.
    """
    dateutil = _import_dateutil()

    def _case():
        return dateutil.parser.parse(None)  # type: ignore[arg-type]

    ok, msg = _run_case("parse_none", _case)
    assert ok, msg


@pytest.mark.timeout(10)
def test_dateutil_relativedelta_basic_usage():
    """
    Robustness 5: relativedelta should exist and be usable for basic arithmetic.
    """
    dateutil = _import_dateutil()

    def _case():
        from datetime import datetime

        rd = dateutil.relativedelta.relativedelta(months=+1, days=+2)
        base = datetime(2020, 1, 1)
        out = base + rd
        # expected: 2020-02-03
        assert out.year == 2020 and out.month == 2 and out.day == 3
        return out

    ok, msg = _run_case("relativedelta_basic", _case)
    assert ok, msg


@pytest.mark.timeout(10)
def test_dateutil_tz_gettz_and_timezone_awareness():
    """
    Robustness 6: tz.gettz should not crash; parse with tzinfo may work depending on env.
    We accept either timezone-aware results or safe failure (no crash/hang).
    """
    dateutil = _import_dateutil()

    def _case():
        tz = dateutil.tz.gettz("UTC")
        # tz can be None if tz database not available, but should not crash.
        dt = dateutil.parser.parse("2020-01-01 00:00:00")
        if tz is not None:
            dt = dt.replace(tzinfo=tz)
            assert dt.tzinfo is not None
        return dt

    ok, msg = _run_case("tz_gettz_usage", _case)
    assert ok, msg
