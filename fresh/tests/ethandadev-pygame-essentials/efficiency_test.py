import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'pygame_essentials'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'check_pygame', 'kind': 'object', 'signature': ''}, {'name': 'Button', 'kind': 'object', 'signature': ''}, {'name': 'Checkbox', 'kind': 'object', 'signature': ''}, {'name': 'Dropdown', 'kind': 'object', 'signature': ''}, {'name': 'Label', 'kind': 'object', 'signature': ''}, {'name': 'ProgressBar', 'kind': 'object', 'signature': ''}, {'name': 'Slider', 'kind': 'object', 'signature': ''}, {'name': 'TextInput', 'kind': 'object', 'signature': ''}, {'name': 'Toggle', 'kind': 'object', 'signature': ''}, {'name': 'Widget', 'kind': 'object', 'signature': ''}, {'name': 'resolve_font', 'kind': 'object', 'signature': ''}, {'name': 'Animation', 'kind': 'object', 'signature': ''}, {'name': 'AnimationSet', 'kind': 'object', 'signature': ''}, {'name': 'Spritesheet', 'kind': 'object', 'signature': ''}, {'name': 'Camera', 'kind': 'object', 'signature': ''}, {'name': 'DebugOverlay', 'kind': 'object', 'signature': ''}]
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

