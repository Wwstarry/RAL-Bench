import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'macos'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'appearance', 'kind': 'object', 'signature': ''}, {'name': 'apps', 'kind': 'object', 'signature': ''}, {'name': 'audio', 'kind': 'object', 'signature': ''}, {'name': 'auth', 'kind': 'object', 'signature': ''}, {'name': 'bluetooth', 'kind': 'object', 'signature': ''}, {'name': 'browser', 'kind': 'object', 'signature': ''}, {'name': 'camera', 'kind': 'object', 'signature': ''}, {'name': 'clipboard', 'kind': 'object', 'signature': ''}, {'name': 'defaults', 'kind': 'object', 'signature': ''}, {'name': 'dialog', 'kind': 'object', 'signature': ''}, {'name': 'dock', 'kind': 'object', 'signature': ''}, {'name': 'document', 'kind': 'object', 'signature': ''}, {'name': 'events', 'kind': 'object', 'signature': ''}, {'name': 'finder', 'kind': 'object', 'signature': ''}, {'name': 'hotkeys', 'kind': 'object', 'signature': ''}, {'name': 'image', 'kind': 'object', 'signature': ''}]
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

