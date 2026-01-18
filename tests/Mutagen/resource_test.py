from __future__ import annotations

import os
import sys
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List

import pytest

ROOT = Path(__file__).resolve().parents[2]

TARGET_ENV = os.getenv("MUTAGEN_TARGET", "reference")
if TARGET_ENV == "reference":
    REPO_ROOT = ROOT / "repositories" / "Mutagen"
elif TARGET_ENV == "generation":
    REPO_ROOT = ROOT / "generation" / "Mutagen"
else:
    raise RuntimeError(f"Unsupported MUTAGEN_TARGET value: {TARGET_ENV}")

if not REPO_ROOT.exists():
    raise RuntimeError(f"Repository root does not exist: {REPO_ROOT}")

if (REPO_ROOT / "mutagen").exists():
    PACKAGE_ROOT = REPO_ROOT
elif (REPO_ROOT / "src" / "mutagen").exists():
    PACKAGE_ROOT = REPO_ROOT / "src"
else:
    raise RuntimeError(f"Could not find 'mutagen' package directory under {REPO_ROOT}")

sys.path.insert(0, str(PACKAGE_ROOT))

from mutagen.easyid3 import EasyID3  # type: ignore[import]
from mutagen.id3 import ID3, TIT2, COMM  # type: ignore[import]


def _create_many_easyid3_files(directory: Path, count: int = 200) -> None:
    """Create many small files with EasyID3 tags to exercise memory usage."""
    long_album_name = "Album " + ("X" * 100)
    for idx in range(count):
        path = directory / f"easy_{idx}.mp3"
        tags = EasyID3()
        tags["title"] = [f"Track {idx}"]
        tags["artist"] = [f"Artist {idx % 20}"]
        tags["album"] = [long_album_name]
        tags["tracknumber"] = [str(idx + 1)]
        tags.save(str(path))


def _repeated_id3_comment_updates(path: Path, iterations: int = 200) -> None:
    """Update a large comment frame many times to exercise memory behavior."""
    tags = ID3()
    tags.add(TIT2(encoding=3, text="Resource Test"))
    tags.save(str(path))

    for i in range(iterations):
        t = ID3(str(path))
        comment_text = "Comment iteration " + str(i) + " - " + ("Y" * 200)
        t.setall(
            "COMM",
            [
                COMM(
                    encoding=3,
                    lang="eng",
                    desc="Test",
                    text=comment_text,
                )
            ],
        )
        t.save()


def test_memory_usage_under_many_easyid3_files(tmp_path: Path) -> None:
    """Ensure that creating many EasyID3-tagged files stays within a memory bound."""
    tracemalloc.start()

    _create_many_easyid3_files(tmp_path, count=200)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    max_allowed_bytes = 200 * 1024 * 1024
    assert peak < max_allowed_bytes


def test_memory_usage_under_repeated_id3_comment_updates(tmp_path: Path) -> None:
    """Ensure that repeated ID3 comment updates do not leak unbounded memory."""
    audio_path = tmp_path / "resource_comment.mp3"

    tracemalloc.start()

    _repeated_id3_comment_updates(audio_path, iterations=200)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    max_allowed_bytes = 200 * 1024 * 1024
    assert peak < max_allowed_bytes
