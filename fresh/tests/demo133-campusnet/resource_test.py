import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'campusnet'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'Config', 'kind': 'object', 'signature': ''}, {'name': 'default_config_path', 'kind': 'object', 'signature': ''}, {'name': 'load_config', 'kind': 'object', 'signature': ''}, {'name': 'Response', 'kind': 'object', 'signature': ''}, {'name': 'Session', 'kind': 'object', 'signature': ''}]
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

