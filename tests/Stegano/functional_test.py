from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

import pytest

# This file lives at:
#   <root>/tests/Stegano/functional_test.py
ROOT = Path(__file__).resolve().parents[2]

# Unified repo root override for the benchmark runner.
REPO_ROOT_ENV = "RACB_REPO_ROOT"
PACKAGE_NAME = "stegano"


def _select_repo_root() -> Path:
    override = os.environ.get(REPO_ROOT_ENV, "").strip()
    if override:
        return Path(override).resolve()

    target = os.environ.get("STEGANO_TARGET", "generated").lower()
    if target == "reference":
        return (ROOT / "repositories" / "Stegano").resolve()
    return (ROOT / "generation" / "Stegano").resolve()


REPO_ROOT = _select_repo_root()
if not REPO_ROOT.exists():
    pytest.skip("Target repository does not exist: {}".format(REPO_ROOT), allow_module_level=True)

# Support both layouts:
#   - repo_root/stegano/__init__.py
#   - repo_root/src/stegano/__init__.py
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

# Import from the selected repository (reference or generated)
try:
    from stegano import lsb, red, exifHeader, wav  # type: ignore
    from stegano.lsb import generators  # type: ignore
except Exception as exc:
    pytest.skip("Failed to import stegano: {}".format(exc), allow_module_level=True)

# Sample files are always taken from the reference Stegano repo
REFERENCE_ROOT = ROOT / "repositories" / "Stegano"
SAMPLE_FILES = REFERENCE_ROOT / "tests" / "sample-files"

LENNA_PNG = SAMPLE_FILES / "Lenna.png"
EXIF_JPEG = SAMPLE_FILES / "20160505T130442.jpg"
WAV_FILES: List[Path] = list(SAMPLE_FILES.glob("*.wav"))


def _ensure_image_samples_exist() -> None:
    assert LENNA_PNG.exists(), "Missing sample file: {}".format(LENNA_PNG)
    assert EXIF_JPEG.exists(), "Missing sample file: {}".format(EXIF_JPEG)


def _pick_sample_wav() -> Path:
    if not WAV_FILES:
        pytest.skip("No WAV sample files found in {}".format(SAMPLE_FILES))
    return WAV_FILES[0]


# ---------------------------------------------------------
# LSB backend
# ---------------------------------------------------------

def test_lsb_hide_and_reveal_text(tmp_path: Path) -> None:
    """lsb.hide(..., str) then lsb.reveal(...) returns the same string."""
    _ensure_image_samples_exist()

    secret = "hello world"
    output = tmp_path / "lsb_lenna.png"

    encoded_img = lsb.hide(str(LENNA_PNG), secret)
    encoded_img.save(str(output))

    revealed = lsb.reveal(str(output))
    assert revealed == secret


def test_lsb_hide_and_reveal_with_generator(tmp_path: Path) -> None:
    """lsb hide/reveal with a deterministic generator."""
    _ensure_image_samples_exist()

    secret = "generator secret"
    output = tmp_path / "lsb_generator.png"

    gen = generators.eratosthenes()
    encoded_img = lsb.hide(str(LENNA_PNG), secret, generator=gen)
    encoded_img.save(str(output))

    gen2 = generators.eratosthenes()
    revealed = lsb.reveal(str(output), generator=gen2)
    assert revealed == secret


def test_lsb_hide_and_reveal_long_ascii_text(tmp_path: Path) -> None:
    """LSB should roundtrip a longer ASCII text message (still < typical capacity)."""
    _ensure_image_samples_exist()

    secret = "This is a longer secret message with punctuation: 12345, hello-world!"
    output = tmp_path / "lsb_long.png"

    encoded_img = lsb.hide(str(LENNA_PNG), secret)
    encoded_img.save(str(output))

    revealed = lsb.reveal(str(output))
    assert revealed == secret


def test_lsb_reveal_from_image_object() -> None:
    """lsb.reveal should work when passed a PIL.Image object (common API usage)."""
    _ensure_image_samples_exist()

    secret = "object input"
    img_obj = lsb.hide(str(LENNA_PNG), secret)
    revealed = lsb.reveal(img_obj)
    assert revealed == secret


# ---------------------------------------------------------
# Red-channel backend
# ---------------------------------------------------------

def test_red_hide_and_reveal_text(tmp_path: Path) -> None:
    """red.hide(..., str) then red.reveal(...) returns the same string."""
    _ensure_image_samples_exist()

    secret = "red secret"
    output = tmp_path / "red_lenna.png"

    encoded_img = red.hide(str(LENNA_PNG), secret)
    encoded_img.save(str(output))

    revealed = red.reveal(str(output))
    assert revealed == secret


def test_red_hide_and_reveal_extended_latin_text(tmp_path: Path) -> None:
    """Red backend stores per-char ord() into a byte channel; Latin-1 chars like 'é' are valid."""
    _ensure_image_samples_exist()

    secret = "Café au lait"
    output = tmp_path / "red_latin.png"

    encoded_img = red.hide(str(LENNA_PNG), secret)
    encoded_img.save(str(output))

    revealed = red.reveal(str(output))
    assert revealed == secret


# ---------------------------------------------------------
# EXIF-header backend
# ---------------------------------------------------------

def test_exif_hide_and_reveal_bytes(tmp_path: Path) -> None:
    """exifHeader.hide writes output file, exifHeader.reveal returns original bytes."""
    _ensure_image_samples_exist()

    secret = b"exif secret bytes"
    output = tmp_path / "exif_out.jpg"

    exifHeader.hide(str(EXIF_JPEG), str(output), secret_message=secret)
    assert output.exists()
    assert output.stat().st_size > 0

    revealed = exifHeader.reveal(str(output))
    assert revealed == secret


def test_exif_hide_two_outputs_with_different_payloads(tmp_path: Path) -> None:
    """Write two different EXIF-hidden files (two independent happy-path scenarios)."""
    _ensure_image_samples_exist()

    out1 = tmp_path / "exif_one.jpg"
    out2 = tmp_path / "exif_two.jpg"

    secret1 = b"payload-one"
    secret2 = b"payload-two"

    exifHeader.hide(str(EXIF_JPEG), str(out1), secret_message=secret1)
    exifHeader.hide(str(EXIF_JPEG), str(out2), secret_message=secret2)

    assert out1.exists() and out1.stat().st_size > 0
    assert out2.exists() and out2.stat().st_size > 0

    assert exifHeader.reveal(str(out1)) == secret1
    assert exifHeader.reveal(str(out2)) == secret2


# ---------------------------------------------------------
# WAV backend
# ---------------------------------------------------------

def test_wav_hide_and_reveal_text(tmp_path: Path) -> None:
    """wav.hide writes output WAV; wav.reveal returns the same string."""
    wav_in = _pick_sample_wav()

    secret = "wav secret"
    output = tmp_path / "out.wav"

    wav.hide(str(wav_in), secret, str(output))
    assert output.exists()
    assert output.stat().st_size > 0

    revealed = wav.reveal(str(output))
    assert revealed == secret


def test_wav_hide_and_reveal_short_text(tmp_path: Path) -> None:
    """A short message should also roundtrip."""
    wav_in = _pick_sample_wav()

    secret = "ok"
    output = tmp_path / "out_short.wav"

    wav.hide(str(wav_in), secret, str(output))
    assert output.exists()
    assert output.stat().st_size > 0

    revealed = wav.reveal(str(output))
    assert revealed == secret


def test_wav_hide_and_reveal_longer_text(tmp_path: Path) -> None:
    """Roundtrip a longer ASCII message via WAV backend."""
    wav_in = _pick_sample_wav()

    secret = "WAV backend long message: 1234567890 abcdefghijklmnopqrstuvwxyz"
    output = tmp_path / "out_long.wav"

    wav.hide(str(wav_in), secret, str(output))
    assert output.exists()
    assert output.stat().st_size > 0

    revealed = wav.reveal(str(output))
    assert revealed == secret


# ---------------------------------------------------------
# Cross-backend sanity: written files are non-empty
# ---------------------------------------------------------

def test_lsb_and_red_outputs_are_files(tmp_path: Path) -> None:
    """Ensure image-encoding backends produce files that can be written to disk."""
    _ensure_image_samples_exist()

    out_lsb = tmp_path / "lsb_file.png"
    out_red = tmp_path / "red_file.png"

    lsb.hide(str(LENNA_PNG), "x").save(str(out_lsb))
    red.hide(str(LENNA_PNG), "y").save(str(out_red))

    assert out_lsb.exists()
    assert out_red.exists()
    assert out_lsb.stat().st_size > 0
    assert out_red.stat().st_size > 0
