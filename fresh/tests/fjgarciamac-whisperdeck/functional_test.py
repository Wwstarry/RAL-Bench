import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'whisperdeck.audio'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'AudioError', 'kind': 'class', 'signature': 'class'}, {'name': 'load_wav', 'kind': 'function', 'signature': '(path)'}, {'name': 'duration_seconds', 'kind': 'function', 'signature': '(path)'}, {'name': 'trim', 'kind': 'function', 'signature': '(path, out_path, start_s, end_s)'}, {'name': 'rms_levels', 'kind': 'function', 'signature': '(path, window_s)'}]
CONSTANTS = {}


def load_module():
    repo = Path(os.environ["RACB_REPO_ROOT"]).resolve()
    root = repo if MODULE_ROOT == "." else repo / MODULE_ROOT
    sys.path.insert(0, str(root))
    return importlib.import_module(MODULE)


def test_public_module_imports():
    assert load_module().__name__ == MODULE


@pytest.mark.parametrize("spec", SYMBOLS)
def test_declared_public_symbol(spec):
    value = getattr(load_module(), spec["name"])
    if spec["kind"] == "class":
        assert inspect.isclass(value)
    elif spec["kind"] == "function":
        assert callable(value)
    else:
        assert value is not None


@pytest.mark.parametrize("name, expected", list(CONSTANTS.items()))
def test_public_literal_constant(name, expected):
    assert getattr(load_module(), name) == expected


def test_wav_load_duration_trim_and_rms(tmp_path):
    import struct
    import wave

    audio = load_module()
    source = tmp_path / "source.wav"
    frames = [0, 1000, -1000, 2000, -2000, 0, 500, -500]
    with wave.open(str(source), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8)
        stream.writeframes(struct.pack("<8h", *frames))
    rate, channels, loaded = audio.load_wav(source)
    assert (rate, channels, loaded) == (8, 1, frames)
    assert audio.duration_seconds(source) == 1.0
    target = tmp_path / "trimmed.wav"
    assert audio.trim(source, target, 0.25, 0.75) == target
    assert audio.duration_seconds(target) == 0.5
    assert len(audio.rms_levels(source, window_s=0.25)) == 3

