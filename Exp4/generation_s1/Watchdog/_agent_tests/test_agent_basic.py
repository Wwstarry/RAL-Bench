import os
import time
from pathlib import Path

import pytest

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class RecordingHandler(FileSystemEventHandler):
    def __init__(self):
        self.events = []

    def on_created(self, event):
        self.events.append(("created", os.path.abspath(event.src_path), event.is_directory))

    def on_modified(self, event):
        self.events.append(("modified", os.path.abspath(event.src_path), event.is_directory))

    def on_deleted(self, event):
        self.events.append(("deleted", os.path.abspath(event.src_path), event.is_directory))


def wait_for(predicate, timeout=3.0, interval=0.02):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if predicate():
            return True
        time.sleep(interval)
    return False


@pytest.fixture
def observer():
    obs = Observer(timeout=0.05)
    try:
        yield obs
    finally:
        obs.stop()
        obs.join(2.0)


def test_imports():
    import watchdog
    import watchdog.events
    import watchdog.observers

    assert hasattr(watchdog, "Observer")
    assert hasattr(watchdog.events, "FileSystemEventHandler")


def test_non_recursive_ignores_subdir(observer, tmp_path: Path):
    h = RecordingHandler()
    observer.schedule(h, str(tmp_path), recursive=False)
    observer.start()

    sub = tmp_path / "sub"
    sub.mkdir()
    f = sub / "a.txt"
    f.write_text("x", encoding="utf-8")

    assert not wait_for(lambda: any(e[1] == str(f.resolve()) and e[0] == "created" for e in h.events), timeout=1.0)


def test_recursive_sees_subdir_file(observer, tmp_path: Path):
    h = RecordingHandler()
    observer.schedule(h, str(tmp_path), recursive=True)
    observer.start()

    sub = tmp_path / "sub"
    sub.mkdir()
    f = sub / "a.txt"
    f.write_text("x", encoding="utf-8")

    assert wait_for(lambda: any(e[0] == "created" and e[1] == str(f.resolve()) for e in h.events), timeout=3.0)

    # Modify
    f.write_text("xy", encoding="utf-8")
    assert wait_for(lambda: any(e[0] == "modified" and e[1] == str(f.resolve()) for e in h.events), timeout=3.0)

    # Delete
    f.unlink()
    assert wait_for(lambda: any(e[0] == "deleted" and e[1] == str(f.resolve()) for e in h.events), timeout=3.0)


def test_no_initial_created_for_existing_file(tmp_path: Path):
    f = tmp_path / "preexist.txt"
    f.write_text("hello", encoding="utf-8")

    h = RecordingHandler()
    obs = Observer(timeout=0.05)
    obs.schedule(h, str(tmp_path), recursive=False)
    obs.start()
    try:
        time.sleep(0.3)
        assert not any(e[0] == "created" and e[1] == str(f.resolve()) for e in h.events)
    finally:
        obs.stop()
        obs.join(2.0)


def test_stop_prevents_more_events(tmp_path: Path):
    h = RecordingHandler()
    obs = Observer(timeout=0.05)
    obs.schedule(h, str(tmp_path), recursive=False)
    obs.start()

    f = tmp_path / "x.txt"
    f.write_text("1", encoding="utf-8")
    assert wait_for(lambda: any(e[0] == "created" and e[1] == str(f.resolve()) for e in h.events), timeout=3.0)

    obs.stop()
    obs.join(2.0)

    # After stop, new changes should not be observed.
    g = tmp_path / "y.txt"
    g.write_text("2", encoding="utf-8")
    time.sleep(0.3)
    assert not any(e[1] == str(g.resolve()) for e in h.events)


def test_multiple_handlers_receive(tmp_path: Path):
    obs = Observer(timeout=0.05)
    h1 = RecordingHandler()
    h2 = RecordingHandler()
    obs.schedule(h1, str(tmp_path), recursive=False)
    obs.schedule(h2, str(tmp_path), recursive=False)
    obs.start()
    try:
        f = tmp_path / "multi.txt"
        f.write_text("x", encoding="utf-8")
        assert wait_for(lambda: any(e[0] == "created" and e[1] == str(f.resolve()) for e in h1.events), timeout=3.0)
        assert wait_for(lambda: any(e[0] == "created" and e[1] == str(f.resolve()) for e in h2.events), timeout=3.0)
    finally:
        obs.stop()
        obs.join(2.0)