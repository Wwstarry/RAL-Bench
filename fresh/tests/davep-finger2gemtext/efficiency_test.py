import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'finger2gemtext'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'version', 'kind': 'object', 'signature': ''}, {'name': 'AvailableServicesFilter', 'kind': 'object', 'signature': ''}, {'name': 'finger_to_gemtext', 'kind': 'object', 'signature': ''}, {'name': 'FingerFilter', 'kind': 'object', 'signature': ''}, {'name': 'UserListFilter', 'kind': 'object', 'signature': ''}]
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

