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


def test_repeated_import_lookup_is_bounded():
    start = time.perf_counter()
    module = load_module()
    for _ in range(2000):
        for spec in SYMBOLS[:8]:
            getattr(module, spec["name"])
    assert time.perf_counter() - start < 10.0

