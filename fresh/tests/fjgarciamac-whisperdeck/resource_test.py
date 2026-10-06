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


def test_public_surface_is_finite():
    module = load_module()
    names = dir(module)
    assert MODULE.split(".")[-1] in module.__name__
    assert len(names) < 10000

