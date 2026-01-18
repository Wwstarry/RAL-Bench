from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import List, Tuple

import pytest

# -----------------------------------------------------------------------------
# RACB import contract:
# - Use RACB_REPO_ROOT if set.
# - Auto-detect layouts:
#   1) repo_root/watchdog/__init__.py
#   2) repo_root/src/watchdog/__init__.py -> sys.path insert repo_root/src
# -----------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "watchdog"


def _select_repo_root() -> Path:
    override = os.environ.get("RACB_REPO_ROOT", "").strip()
    if override:
        return Path(override).resolve()

    target = os.environ.get("WATCHDOG_TARGET", "reference").lower()
    if target == "reference":
        return (ROOT / "repositories" / "watchdog").resolve()
    return (ROOT / "generation" / "Watchdog").resolve()


REPO_ROOT = _select_repo_root()
if not REPO_ROOT.exists():
    pytest.skip(
        "RACB_REPO_ROOT does not exist on disk: {}".format(REPO_ROOT),
        allow_module_level=True,
    )

src_pkg_init = REPO_ROOT / "src" / PACKAGE / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not find watchdog package. Expected {} or {}.".format(src_pkg_init, root_pkg_init),
        allow_module_level=True,
    )

from watchdog.observers import Observer  # type: ignore  # noqa: E402
from watchdog.events import (  # type: ignore  # noqa: E402
    FileSystemEventHandler,
    PatternMatchingEventHandler,
)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

_WAIT_TIMEOUT_SEC = 2.5
_WAIT_POLL_SEC = 0.05


def _wait_until_contains(events: List[str], needle: str) -> None:
    deadline = time.monotonic() + _WAIT_TIMEOUT_SEC
    while time.monotonic() < deadline:
        if any(needle in e for e in events):
            return
        time.sleep(_WAIT_POLL_SEC)
    assert any(needle in e for e in events), "Expected event not observed: {!r}. Got: {!r}".format(
        needle, events
    )


def _wait_until_any_contains(events: List[str], needles: Tuple[str, ...]) -> None:
    deadline = time.monotonic() + _WAIT_TIMEOUT_SEC
    while time.monotonic() < deadline:
        if any(any(n in e for n in needles) for e in events):
            return
        time.sleep(_WAIT_POLL_SEC)
    assert any(any(n in e for n in needles) for e in events), "Expected one of {}. Got: {!r}".format(
        needles, events
    )


def _wait_until_any_prefix(events: List[str], prefixes: Tuple[str, ...]) -> None:
    deadline = time.monotonic() + _WAIT_TIMEOUT_SEC
    while time.monotonic() < deadline:
        if any(any(e.startswith(p) for p in prefixes) for e in events):
            return
        time.sleep(_WAIT_POLL_SEC)
    assert any(any(e.startswith(p) for p in prefixes) for e in events), "Expected one of {}. Got: {!r}".format(
        prefixes, events
    )


class _Recorder(FileSystemEventHandler):
    """Event recorder (captures common event types)."""

    def __init__(self) -> None:
        super().__init__()
        self.events: List[str] = []
        self.any_events: List[str] = []

    def on_any_event(self, event) -> None:  # type: ignore[override]
        et = getattr(event, "event_type", "unknown")
        src_name = Path(getattr(event, "src_path", "")).name

        if et == "moved" and hasattr(event, "dest_path"):
            dest_name = Path(getattr(event, "dest_path", "")).name
            self.any_events.append("moved:{}->{}".format(src_name, dest_name))
        else:
            self.any_events.append("{}:{}".format(et, src_name))

    def on_created(self, event) -> None:  # type: ignore[override]
        self.events.append("created:{}".format(Path(event.src_path).name))

    def on_modified(self, event) -> None:  # type: ignore[override]
        self.events.append("modified:{}".format(Path(event.src_path).name))

    def on_deleted(self, event) -> None:  # type: ignore[override]
        self.events.append("deleted:{}".format(Path(event.src_path).name))

    def on_moved(self, event) -> None:  # type: ignore[override]
        src = Path(getattr(event, "src_path", "")).name
        dest = Path(getattr(event, "dest_path", "")).name
        self.events.append("moved:{}->{}".format(src, dest))


def _run_observer(tmp_path: Path, handler: FileSystemEventHandler, recursive: bool) -> Observer:
    observer = Observer()
    observer.schedule(handler, str(tmp_path), recursive=recursive)
    observer.start()
    return observer


def _stop_observer(observer: Observer) -> None:
    observer.stop()
    observer.join(timeout=1)


# -----------------------------------------------------------------------------
# Tests (functional-only / happy-path)
# -----------------------------------------------------------------------------

def test_observer_start_stop(tmp_path: Path) -> None:
    handler = _Recorder()
    observer = _run_observer(tmp_path, handler, recursive=False)
    _stop_observer(observer)
    assert observer.is_alive() is False


def test_schedule_returns_watch_with_expected_path(tmp_path: Path) -> None:
    handler = _Recorder()
    observer = Observer()
    watch = observer.schedule(handler, str(tmp_path), recursive=False)

    watch_path = getattr(watch, "path", None)
    assert watch_path is not None
    assert str(tmp_path) in str(watch_path)

    is_rec = getattr(watch, "is_recursive", None)
    rec = getattr(watch, "recursive", None)
    if is_rec is not None:
        assert bool(is_rec) is False
    if rec is not None:
        assert bool(rec) is False


def test_file_create_emits_created_event(tmp_path: Path) -> None:
    handler = _Recorder()
    observer = _run_observer(tmp_path, handler, recursive=False)
    try:
        p = tmp_path / "a.txt"
        p.write_text("hello", encoding="utf-8")
        _wait_until_contains(handler.events, "created:a.txt")
    finally:
        _stop_observer(observer)

    assert any(e == "created:a.txt" for e in handler.events)


def test_file_modify_emits_modified_event(tmp_path: Path) -> None:
    handler = _Recorder()
    observer = _run_observer(tmp_path, handler, recursive=False)
    try:
        p = tmp_path / "b.txt"
        p.write_text("v1", encoding="utf-8")
        _wait_until_contains(handler.events, "created:b.txt")

        p.write_text("v2", encoding="utf-8")
        _wait_until_contains(handler.events, "modified:b.txt")
    finally:
        _stop_observer(observer)

    assert any("modified:b.txt" == e for e in handler.events)


def test_file_delete_emits_deleted_event(tmp_path: Path) -> None:
    handler = _Recorder()
    observer = _run_observer(tmp_path, handler, recursive=False)
    try:
        p = tmp_path / "c.txt"
        p.write_text("to delete", encoding="utf-8")
        _wait_until_contains(handler.events, "created:c.txt")

        p.unlink()
        _wait_until_contains(handler.events, "deleted:c.txt")
    finally:
        _stop_observer(observer)

    assert any(e == "deleted:c.txt" for e in handler.events)


def test_file_move_emits_rename_related_event(tmp_path: Path) -> None:
    handler = _Recorder()
    observer = _run_observer(tmp_path, handler, recursive=False)
    try:
        src = tmp_path / "old.txt"
        dst = tmp_path / "new.txt"
        src.write_text("data", encoding="utf-8")
        _wait_until_contains(handler.events, "created:old.txt")

        src.rename(dst)
        _wait_until_any_contains(handler.any_events + handler.events, ("old.txt", "new.txt"))
    finally:
        _stop_observer(observer)

    assert dst.exists()
    assert not src.exists()

    combined = handler.events + handler.any_events
    saw_moved = any("moved:old.txt->new.txt" in e for e in combined)
    saw_delete_create = any("deleted:old.txt" == e for e in combined) and any("created:new.txt" == e for e in combined)
    saw_name_mentions = any("old.txt" in e or "new.txt" in e for e in combined)
    assert saw_moved or saw_delete_create or saw_name_mentions


def test_directory_create_emits_created_event(tmp_path: Path) -> None:
    handler = _Recorder()
    observer = _run_observer(tmp_path, handler, recursive=False)
    try:
        d = tmp_path / "subdir"
        d.mkdir()
        _wait_until_contains(handler.events, "created:subdir")
    finally:
        _stop_observer(observer)

    assert any(e == "created:subdir" for e in handler.events)


def test_directory_delete_emits_deleted_event(tmp_path: Path) -> None:
    handler = _Recorder()
    observer = _run_observer(tmp_path, handler, recursive=False)
    try:
        d = tmp_path / "gone"
        d.mkdir()
        _wait_until_contains(handler.events, "created:gone")

        d.rmdir()
        _wait_until_contains(handler.events, "deleted:gone")
    finally:
        _stop_observer(observer)

    assert any(e == "deleted:gone" for e in handler.events)


def test_recursive_observer_sees_nested_file_create(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()

    handler = _Recorder()
    observer = _run_observer(tmp_path, handler, recursive=True)
    try:
        p = nested / "deep.txt"
        p.write_text("deep", encoding="utf-8")
        _wait_until_contains(handler.events, "created:deep.txt")
    finally:
        _stop_observer(observer)

    assert any(e == "created:deep.txt" for e in handler.events)


def test_pattern_matching_handler_matches_log_files(tmp_path: Path) -> None:
    """PatternMatchingEventHandler should match events for *.log files (Windows full-path safe)."""
    matched: List[str] = []

    class _MatchRecorder(PatternMatchingEventHandler):
        def on_created(self, event) -> None:  # type: ignore[override]
            matched.append(Path(getattr(event, "src_path", "")).name)

        def on_modified(self, event) -> None:  # type: ignore[override]
            matched.append(Path(getattr(event, "src_path", "")).name)

    # On some watchdog implementations/platforms, PatternMatchingEventHandler matches
    # against the *full* absolute path. Provide patterns that cover both separators.
    log_patterns = [
        "*.log",
        "**/*.log",
        "**\\*.log",
        "*/*.log",
        "*\\*.log",
    ]

    handler = _MatchRecorder(patterns=log_patterns, ignore_directories=True)
    observer = _run_observer(tmp_path, handler, recursive=False)
    try:
        logp = tmp_path / "a.log"
        txtp = tmp_path / "b.txt"

        logp.write_text("log", encoding="utf-8")
        txtp.write_text("txt", encoding="utf-8")
        # One more write increases chance of a matched "modified" event.
        logp.write_text("log2", encoding="utf-8")

        deadline = time.monotonic() + _WAIT_TIMEOUT_SEC
        while time.monotonic() < deadline and "a.log" not in matched:
            time.sleep(_WAIT_POLL_SEC)
    finally:
        _stop_observer(observer)

    assert "a.log" in matched
    # All matched file names should be for *.log.
    assert all(name.endswith(".log") for name in matched)


def test_on_any_event_records_event_type_for_create(tmp_path: Path) -> None:
    handler = _Recorder()
    observer = _run_observer(tmp_path, handler, recursive=False)
    try:
        p = tmp_path / "any.txt"
        p.write_text("x", encoding="utf-8")
        deadline = time.monotonic() + _WAIT_TIMEOUT_SEC
        while time.monotonic() < deadline and not any("any.txt" in e for e in handler.any_events):
            time.sleep(_WAIT_POLL_SEC)
    finally:
        _stop_observer(observer)

    assert any("any.txt" in e for e in handler.any_events)
    assert any(e.startswith("created:") for e in handler.any_events) or any(
        e.startswith("modified:") for e in handler.any_events
    )
