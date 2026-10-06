import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'skillsync.classifier'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'classify', 'kind': 'function', 'signature': '(skill, config)'}, {'name': 'classify_all', 'kind': 'function', 'signature': '(skills, config)'}]
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

