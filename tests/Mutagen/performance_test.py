from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Dict, List

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
from mutagen.id3 import ID3, TIT2  # type: ignore[import]


def test_bulk_easyid3_write_and_read_performance(tmp_path: Path) -> None:
    """
    Create and read many tag-only MP3 files using EasyID3 to measure throughput.

    This test is a coarse performance check with a generous upper bound so that
    it is stable across different machines while still providing a baseline.
    """
    num_files = 150
    paths: List[Path] = []

    start = time.perf_counter()

    for idx in range(num_files):
        path = tmp_path / f"file_{idx}.mp3"
        tags = EasyID3()
        tags["title"] = [f"Song {idx}"]
        tags["artist"] = [f"Artist {idx % 10}"]
        tags["album"] = ["Performance Album"]
        tags["tracknumber"] = [str(idx + 1)]
        tags.save(str(path))
        paths.append(path)

    for path in paths:
        tags = EasyID3(str(path))
        assert "title" in tags
        assert "artist" in tags

    elapsed = time.perf_counter() - start
    assert elapsed < 20.0


def test_repeated_id3_updates_performance(tmp_path: Path) -> None:
    """
    Repeatedly update ID3 text frames on a single file and ensure it is fast enough.
    """
    audio_path = tmp_path / "updates.mp3"

    tags = ID3()
    tags.add(TIT2(encoding=3, text="Initial Title"))
    tags.save(str(audio_path))

    iterations = 200

    start = time.perf_counter()

    for i in range(iterations):
        t = ID3(str(audio_path))
        t["TIT2"].text = [f"Title {i}"]
        t.save()

    elapsed = time.perf_counter() - start

    # Ensure that the loop finished within a generous time bound.
    assert elapsed < 20.0

    final_tags = ID3(str(audio_path))
    assert final_tags["TIT2"].text == [f"Title {iterations - 1}"]
