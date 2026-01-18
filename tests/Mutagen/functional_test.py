from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, List

import pytest

# ---------------------------------------------------------------------------
# Repo root resolution (RACB-compatible + local fallback)
#
# RACB requirement (preferred): use RACB_REPO_ROOT and support both layouts:
#   - <repo_root>/mutagen/__init__.py
#   - <repo_root>/src/mutagen/__init__.py
#
# Local fallback (no absolute path hardcode): keep original eval layout:
#   <eval_root>/repositories/Mutagen  OR  <eval_root>/generation/Mutagen
# ---------------------------------------------------------------------------

PACKAGE_NAME = "mutagen"

_racb_root = os.environ.get("RACB_REPO_ROOT", "").strip()
if _racb_root:
    REPO_ROOT = Path(_racb_root).resolve()
else:
    ROOT = Path(__file__).resolve().parents[2]
    target = os.getenv("MUTAGEN_TARGET", "reference").lower()
    if target == "reference":
        REPO_ROOT = ROOT / "repositories" / "Mutagen"
    elif target == "generation":
        REPO_ROOT = ROOT / "generation" / "Mutagen"
    else:
        pytest.skip(
            "Unsupported MUTAGEN_TARGET value: {}".format(target),
            allow_module_level=True,
        )

if not REPO_ROOT.exists():
    pytest.skip(
        "Repository root does not exist: {}".format(REPO_ROOT),
        allow_module_level=True,
    )

src_pkg_init = REPO_ROOT / "src" / PACKAGE_NAME / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE_NAME / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not find '{}' package directory under {} (expected {} or {}).".format(
            PACKAGE_NAME, REPO_ROOT, src_pkg_init, root_pkg_init
        ),
        allow_module_level=True,
    )

try:
    from mutagen.easyid3 import EasyID3  # type: ignore[import]
    from mutagen.id3 import (  # type: ignore[import]
        ID3,
        TIT2,
        TPE1,
        TALB,
        TCON,
        COMM,
        APIC,
    )
except Exception as exc:
    pytest.skip(
        "Failed to import mutagen from {}: {}".format(REPO_ROOT, exc),
        allow_module_level=True,
    )


def _read_easy_tags(path: Path) -> Dict[str, List[str]]:
    """Read tags using EasyID3 and return a plain mapping."""
    tags = EasyID3(str(path))
    return {k: list(v) for k, v in tags.items()}


def _write_easy_tags(path: Path, mapping: Dict[str, List[str]]) -> None:
    """Create/save an EasyID3 tag set to a path (tag-only file)."""
    tags = EasyID3()
    for k, v in mapping.items():
        tags[k] = list(v)
    tags.save(str(path))


# ---------------------------------------------------------------------------
# Core EasyID3 roundtrip tests
# ---------------------------------------------------------------------------

def test_easyid3_basic_tags_roundtrip(tmp_path: Path) -> None:
    """Create a tag-only MP3 file and verify EasyID3 roundtrip for core fields."""
    audio_path = tmp_path / "basic.mp3"

    tags = EasyID3()
    tags["title"] = ["Test Title"]
    tags["artist"] = ["Test Artist"]
    tags["album"] = ["Test Album"]
    tags["tracknumber"] = ["1"]
    tags["date"] = ["2024"]
    tags.save(str(audio_path))

    assert audio_path.exists()

    reloaded = EasyID3(str(audio_path))
    assert reloaded["title"] == ["Test Title"]
    assert reloaded["artist"] == ["Test Artist"]
    assert reloaded["album"] == ["Test Album"]
    assert reloaded["tracknumber"] == ["1"]
    assert reloaded["date"] == ["2024"]


def test_easyid3_update_and_delete_tags(tmp_path: Path) -> None:
    """Modify and delete existing EasyID3 fields and verify persisted changes."""
    audio_path = tmp_path / "update_delete.mp3"

    tags = EasyID3()
    tags["title"] = ["Original Title"]
    tags["artist"] = ["Original Artist"]
    tags["tracknumber"] = ["3/10"]
    tags.save(str(audio_path))

    tags2 = EasyID3(str(audio_path))
    tags2["title"] = ["New Title"]
    del tags2["artist"]
    tags2["tracknumber"] = ["5"]
    tags2.save()

    tags3 = EasyID3(str(audio_path))
    assert tags3["title"] == ["New Title"]
    assert "artist" not in tags3
    assert tags3["tracknumber"] == ["5"]


def test_easyid3_missing_optional_fields_are_absent(tmp_path: Path) -> None:
    """Ensure missing optional fields are simply absent from EasyID3 mappings."""
    audio_path = tmp_path / "missing_optional.mp3"

    _write_easy_tags(audio_path, {"title": ["Only Title"]})
    assert audio_path.exists()

    reloaded = EasyID3(str(audio_path))
    assert reloaded["title"] == ["Only Title"]
    assert "artist" not in reloaded

    mapping = _read_easy_tags(audio_path)
    assert mapping["title"] == ["Only Title"]
    assert "artist" not in mapping


def test_easyid3_multiple_values_for_artist(tmp_path: Path) -> None:
    """Store multiple artist values and verify they are preserved."""
    audio_path = tmp_path / "multi_artist.mp3"

    tags = EasyID3()
    tags["artist"] = ["Artist One", "Artist Two"]
    tags["title"] = ["Collaboration"]
    tags.save(str(audio_path))

    reloaded = EasyID3(str(audio_path))
    assert reloaded["title"] == ["Collaboration"]
    assert reloaded["artist"] == ["Artist One", "Artist Two"]


def test_easyid3_copy_file_and_preserve_tags(tmp_path: Path) -> None:
    """Write tags once, reopen and save again, and ensure tags are preserved."""
    audio_path = tmp_path / "copy_preserve.mp3"

    tags = EasyID3()
    tags["title"] = ["Original"]
    tags["artist"] = ["Persistent Artist"]
    tags.save(str(audio_path))

    reloaded = EasyID3(str(audio_path))
    reloaded.save()

    tags_after = EasyID3(str(audio_path))
    assert tags_after["title"] == ["Original"]
    assert tags_after["artist"] == ["Persistent Artist"]


def test_easyid3_genre_and_albumartist_roundtrip(tmp_path: Path) -> None:
    """Roundtrip common optional fields via EasyID3 (genre/albumartist)."""
    audio_path = tmp_path / "genre_albumartist.mp3"

    tags = EasyID3()
    tags["title"] = ["Tagged Song"]
    tags["artist"] = ["Main Artist"]
    tags["albumartist"] = ["Album Artist"]
    tags["genre"] = ["Rock"]
    tags.save(str(audio_path))

    reloaded = EasyID3(str(audio_path))
    assert reloaded["title"] == ["Tagged Song"]
    assert reloaded["artist"] == ["Main Artist"]
    assert reloaded["albumartist"] == ["Album Artist"]
    assert reloaded["genre"] == ["Rock"]


def test_low_level_id3_written_can_be_read_by_easyid3(tmp_path: Path) -> None:
    """Write low-level ID3 frames and read them back via EasyID3 fields."""
    audio_path = tmp_path / "interop.mp3"

    tags = ID3()
    tags.add(TIT2(encoding=3, text="Interop Title"))
    tags.add(TPE1(encoding=3, text="Interop Artist"))
    tags.add(TALB(encoding=3, text="Interop Album"))
    tags.save(str(audio_path))

    easy = EasyID3(str(audio_path))
    assert easy["title"] == ["Interop Title"]
    assert easy["artist"] == ["Interop Artist"]
    assert easy["album"] == ["Interop Album"]


# ---------------------------------------------------------------------------
# Low-level ID3 frame tests
# ---------------------------------------------------------------------------

def test_low_level_id3_frames_with_comment_and_apic(tmp_path: Path) -> None:
    """Use low-level ID3 frames to store text and embedded artwork."""
    audio_path = tmp_path / "id3_frames.mp3"

    tags = ID3()
    tags.add(TIT2(encoding=3, text="Frame Title"))
    tags.add(TPE1(encoding=3, text="Frame Artist"))
    tags.add(
        COMM(
            encoding=3,
            lang="eng",
            desc="Comment",
            text="This is a test comment.",
        )
    )

    image_data = b"\xff\xd8\xff\x00FAKEJPEGDATA"
    tags.add(
        APIC(
            encoding=3,
            mime="image/jpeg",
            type=3,
            desc="Cover",
            data=image_data,
        )
    )
    tags.save(str(audio_path))

    loaded = ID3(str(audio_path))

    assert "TIT2" in loaded
    assert "TPE1" in loaded
    assert loaded["TIT2"].text == ["Frame Title"]
    assert loaded["TPE1"].text == ["Frame Artist"]

    comments = loaded.getall("COMM")
    assert comments
    comment = comments[0]
    assert comment.lang == "eng"
    assert "test comment" in "".join(comment.text)

    apic_frames = loaded.getall("APIC")
    assert apic_frames
    apic = apic_frames[0]
    assert apic.mime == "image/jpeg"
    assert apic.type == 3
    assert apic.desc == "Cover"
    assert apic.data.startswith(b"\xff\xd8\xff")


def test_id3_overwrite_title_frame(tmp_path: Path) -> None:
    """Overwrite an existing ID3 title frame and ensure the latest text remains."""
    audio_path = tmp_path / "overwrite_title.mp3"

    tags = ID3()
    tags.add(TIT2(encoding=3, text="Old Title"))
    tags.save(str(audio_path))

    tags2 = ID3(str(audio_path))
    tags2["TIT2"].text = ["New Title"]
    tags2.save()

    loaded = ID3(str(audio_path))
    assert loaded["TIT2"].text == ["New Title"]


def test_id3_add_additional_comment_frames(tmp_path: Path) -> None:
    """Attach multiple comment frames and verify they are all present."""
    audio_path = tmp_path / "multi_comment.mp3"

    tags = ID3()
    tags.add(TIT2(encoding=3, text="Commented Track"))
    tags.add(COMM(encoding=3, lang="eng", desc="First", text="First comment."))
    tags.add(COMM(encoding=3, lang="eng", desc="Second", text="Second comment."))
    tags.save(str(audio_path))

    loaded = ID3(str(audio_path))
    comments = loaded.getall("COMM")
    descriptions = {c.desc for c in comments}
    assert descriptions == {"First", "Second"}


def test_id3_add_and_remove_apic_frame(tmp_path: Path) -> None:
    """Add then remove an APIC frame and verify it is correctly deleted."""
    audio_path = tmp_path / "remove_apic.mp3"

    tags = ID3()
    tags.add(TIT2(encoding=3, text="Cover Track"))
    image_data = b"\xff\xd8\xff\x00FAKEJPEGDATA"
    tags.add(
        APIC(
            encoding=3,
            mime="image/jpeg",
            type=3,
            desc="Cover",
            data=image_data,
        )
    )
    tags.save(str(audio_path))

    loaded = ID3(str(audio_path))
    assert loaded.getall("APIC")

    loaded.delall("APIC")
    loaded.save()

    loaded2 = ID3(str(audio_path))
    assert loaded2.getall("APIC") == []


def test_id3_text_frames_album_and_genre_roundtrip(tmp_path: Path) -> None:
    """Roundtrip common text frames (album/genre) using low-level ID3."""
    audio_path = tmp_path / "album_genre.mp3"

    tags = ID3()
    tags.add(TIT2(encoding=3, text="Song X"))
    tags.add(TALB(encoding=3, text="Album Y"))
    tags.add(TCON(encoding=3, text="Jazz"))
    tags.save(str(audio_path))

    loaded = ID3(str(audio_path))
    assert loaded["TIT2"].text == ["Song X"]
    assert loaded["TALB"].text == ["Album Y"]
    assert loaded["TCON"].text == ["Jazz"]
