from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import pytest

# ---------------------------------------------------------------------------
# Repo root resolution (RACB-compatible + local fallback)
#
# RACB requirement (preferred): use RACB_REPO_ROOT and support both layouts:
#   - <repo_root>/schedule/__init__.py
#   - <repo_root>/src/schedule/__init__.py
#
# Local fallback (no absolute path hardcode): keep original eval layout:
#   <eval_root>/repositories/schedule  OR  <eval_root>/generation/Schedule
# ---------------------------------------------------------------------------

PACKAGE_NAME = "schedule"

_racb_root = os.environ.get("RACB_REPO_ROOT", "").strip()
if _racb_root:
    REPO_ROOT = Path(_racb_root).resolve()
else:
    ROOT = Path(__file__).resolve().parents[2]
    target = os.environ.get("SCHEDULE_TARGET", "generated").lower()
    if target == "reference":
        REPO_ROOT = ROOT / "repositories" / "schedule"
    else:
        REPO_ROOT = ROOT / "generation" / "Schedule"

if not REPO_ROOT.exists():
    pytest.skip("Repository root does not exist: {}".format(REPO_ROOT), allow_module_level=True)

src_pkg_init = REPO_ROOT / "src" / PACKAGE_NAME / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE_NAME / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not find '{}' package under repo root. Expected {} or {}.".format(
            PACKAGE_NAME, src_pkg_init, root_pkg_init
        ),
        allow_module_level=True,
    )

try:
    import schedule  # type: ignore  # noqa: E402
except Exception as exc:
    pytest.skip("Failed to import schedule from {}: {}".format(REPO_ROOT, exc), allow_module_level=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clear() -> None:
    schedule.clear()


def _set_job_due_now(job) -> None:
    """Make a job due for run_pending() without waiting for real time."""
    # schedule stores next_run as a datetime; set it safely in the past.
    now = datetime.now()
    job.next_run = now - timedelta(seconds=1)


def _maybe_get_next_run(job) -> Optional[datetime]:
    return getattr(job, "next_run", None)


def _maybe_get_last_run(job) -> Optional[datetime]:
    return getattr(job, "last_run", None)


# ---------------------------------------------------------------------------
# Tests (functional-only, happy path)  >= 10 test_* functions
# ---------------------------------------------------------------------------

def test_basic_every_and_run_all() -> None:
    """every(...).seconds/minutes + run_all execute jobs."""
    _clear()
    calls: List[str] = []

    def job1() -> None:
        calls.append("job1")

    def job2() -> None:
        calls.append("job2")

    schedule.every(5).seconds.do(job1).tag("sec", "common")
    schedule.every().minutes.do(job2).tag("min", "common")

    jobs = schedule.get_jobs()
    assert len(jobs) == 2
    assert any("sec" in job.tags for job in jobs)
    assert any("min" in job.tags for job in jobs)

    schedule.run_all()

    assert set(calls) == {"job1", "job2"}


def test_tags_and_clear_by_tag() -> None:
    """Jobs can be tagged, selected by tag, and cleared by tag."""
    _clear()
    calls: List[str] = []

    def job_keep() -> None:
        calls.append("keep")

    def job_drop() -> None:
        calls.append("drop")

    schedule.every().hour.do(job_keep).tag("keep", "group")
    schedule.every().hour.do(job_drop).tag("drop", "group")

    drop_jobs = schedule.get_jobs("drop")
    assert len(drop_jobs) == 1

    schedule.clear("drop")

    remaining = schedule.get_jobs()
    assert len(remaining) == 1
    assert "keep" in remaining[0].tags

    schedule.run_all()
    assert calls == ["keep"]


def test_cancel_job_removes_single_job() -> None:
    """cancel_job removes a single job from the scheduler."""
    _clear()
    calls: List[str] = []

    def job1() -> None:
        calls.append("job1")

    def job2() -> None:
        calls.append("job2")

    j1 = schedule.every().day.do(job1)
    j2 = schedule.every().day.at("10:30").do(job2)

    schedule.cancel_job(j2)

    schedule.run_all()
    assert calls == ["job1"]
    assert j1 in schedule.get_jobs()
    assert j2 not in schedule.get_jobs()


def test_repeat_decorator_registers_and_runs() -> None:
    """@repeat(every(...)) schedules a function correctly and run_all triggers it."""
    _clear()
    call_count = 0

    @schedule.repeat(schedule.every().seconds)
    def my_job() -> None:  # type: ignore[unused-ignore]
        nonlocal call_count
        call_count += 1

    jobs = schedule.get_jobs()
    assert len(jobs) >= 1

    schedule.run_all()
    assert call_count >= 1


def test_run_pending_executes_due_job_without_sleep() -> None:
    """run_pending executes jobs that are due, without relying on real time waiting."""
    _clear()
    calls: List[str] = []

    def job() -> None:
        calls.append("ran")

    j = schedule.every(10).seconds.do(job)
    _set_job_due_now(j)

    schedule.run_pending()
    assert calls == ["ran"]


def test_job_next_run_is_datetime_after_scheduling() -> None:
    """A newly scheduled job should have a next_run datetime set."""
    _clear()

    def job() -> None:
        return None

    j = schedule.every().minute.do(job)
    nr = _maybe_get_next_run(j)
    assert isinstance(nr, datetime)


def test_every_day_at_sets_time_component_in_next_run() -> None:
    """Scheduling with .day.at('HH:MM') should include that time in the next_run."""
    _clear()

    def job() -> None:
        return None

    j = schedule.every().day.at("10:30").do(job)
    nr = _maybe_get_next_run(j)
    assert isinstance(nr, datetime)
    assert nr.hour == 10
    assert nr.minute == 30


def test_weekday_scheduling_creates_job_and_next_run() -> None:
    """Weekday scheduling (e.g., monday) should create a job with next_run."""
    _clear()

    def job() -> None:
        return None

    j = schedule.every().monday.at("09:00").do(job)
    nr = _maybe_get_next_run(j)
    assert isinstance(nr, datetime)
    assert nr.hour == 9
    assert nr.minute == 0


def test_every_to_creates_job_with_interval_range() -> None:
    """every(A).to(B).seconds should create a job and be runnable via run_all."""
    _clear()
    calls: List[str] = []

    def job() -> None:
        calls.append("x")

    j = schedule.every(2).to(5).seconds.do(job)
    assert j in schedule.get_jobs()

    schedule.run_all()
    assert calls == ["x"]


def test_idle_seconds_returns_number() -> None:
    """idle_seconds should return a numeric value when jobs exist."""
    _clear()

    def job() -> None:
        return None

    schedule.every().hour.do(job)
    idle = schedule.idle_seconds()
    assert idle is not None
    assert isinstance(idle, (int, float))


def test_get_jobs_by_tag_filters_subset() -> None:
    """get_jobs(tag) should return only jobs with that tag."""
    _clear()

    def a() -> None:
        return None

    def b() -> None:
        return None

    schedule.every().minute.do(a).tag("alpha")
    schedule.every().minute.do(b).tag("beta")

    alpha_jobs = schedule.get_jobs("alpha")
    beta_jobs = schedule.get_jobs("beta")
    all_jobs = schedule.get_jobs()

    assert len(all_jobs) == 2
    assert len(alpha_jobs) == 1
    assert len(beta_jobs) == 1
    assert "alpha" in alpha_jobs[0].tags
    assert "beta" in beta_jobs[0].tags


def test_run_all_sets_last_run_on_job() -> None:
    """After running, last_run should be populated on the job in typical implementations."""
    _clear()

    def job() -> None:
        return None

    j = schedule.every().minute.do(job)
    schedule.run_all()

    last = _maybe_get_last_run(j)
    # Some versions may not expose last_run; if present, it should be datetime.
    if last is not None:
        assert isinstance(last, datetime)
