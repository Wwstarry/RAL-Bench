import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'rotationledger'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'annotations', 'kind': 'object', 'signature': ''}, {'name': 'Finding', 'kind': 'object', 'signature': ''}, {'name': 'scan_line', 'kind': 'object', 'signature': ''}, {'name': 'CharClasses', 'kind': 'object', 'signature': ''}, {'name': 'classify', 'kind': 'object', 'signature': ''}, {'name': 'looks_random', 'kind': 'object', 'signature': ''}, {'name': 'shannon_entropy', 'kind': 'object', 'signature': ''}, {'name': 'Lifetime', 'kind': 'object', 'signature': ''}, {'name': 'reconstruct', 'kind': 'object', 'signature': ''}, {'name': 'Commit', 'kind': 'object', 'signature': ''}, {'name': 'DiffLine', 'kind': 'object', 'signature': ''}, {'name': 'parse_log', 'kind': 'object', 'signature': ''}]
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

