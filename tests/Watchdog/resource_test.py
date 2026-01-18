from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("WATCHDOG_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "watchdog" / "src"
else:
    REPO_ROOT = ROOT / "generation" / "Watchdog"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from watchdog.observers import Observer  # type: ignore  # noqa: E402
from watchdog.events import FileSystemEventHandler  # type: ignore  # noqa: E402


class _Recorder(FileSystemEventHandler):
    """Record created file names in a recursive directory structure."""

    def __init__(self) -> None:
        super().__init__()
        self.created: list[str] = []

    def on_created(self, event) -> None:  # type: ignore[override]
        self.created.append(Path(event.src_path).name)


def test_recursive_directory_events(tmp_path: Path) -> None:
    """Recursive observer should record events in subdirectories."""
    handler = _Recorder()
    obs = Observer()
    obs.schedule(handler, str(tmp_path), recursive=True)
    obs.start()

    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "inner.txt").write_text("hello")
    time.sleep(0.3)

    obs.stop()
    obs.join(timeout=1)

    assert "inner.txt" in handler.created
