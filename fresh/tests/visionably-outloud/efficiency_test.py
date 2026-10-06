import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'outloud'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'annotations', 'kind': 'object', 'signature': ''}, {'name': 'Optional', 'kind': 'object', 'signature': ''}, {'name': 'Result', 'kind': 'object', 'signature': ''}, {'name': 'Document', 'kind': 'object', 'signature': ''}, {'name': 'features', 'kind': 'object', 'signature': ''}, {'name': 'load_catalogue', 'kind': 'object', 'signature': ''}, {'name': 'run_rules', 'kind': 'object', 'signature': ''}, {'name': 'check', 'kind': 'function', 'signature': '(path, source, only, skip, layers)'}]
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

