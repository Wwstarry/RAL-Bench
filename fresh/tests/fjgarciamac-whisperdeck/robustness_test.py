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


def test_repeated_import_is_stable():
    first = load_module()
    assert importlib.import_module(MODULE) is first


def test_missing_public_name_raises_attribute_error():
    with pytest.raises(AttributeError):
        getattr(load_module(), "__ral_bench_missing_public_name__")


@pytest.mark.parametrize("spec", SYMBOLS)
def test_public_callables_are_introspectable(spec):
    value = getattr(load_module(), spec["name"])
    if spec["kind"] == "function":
        inspect.signature(value)


def test_missing_wav_and_unsupported_width_raise_audio_error(tmp_path):
    import wave

    audio = load_module()
    with pytest.raises(audio.AudioError):
        audio.load_wav(tmp_path / "missing.wav")
    bad = tmp_path / "bad.wav"
    with wave.open(str(bad), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(1)
        stream.setframerate(8)
        stream.writeframes(b"\x00\x01")
    with pytest.raises(audio.AudioError, match="16-bit"):
        audio.load_wav(bad)

