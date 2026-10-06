import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'hexmap_web'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'colour', 'kind': 'object', 'signature': ''}, {'name': 'fmt', 'kind': 'object', 'signature': ''}, {'name': 'geometry', 'kind': 'object', 'signature': ''}, {'name': 'hexbin', 'kind': 'object', 'signature': ''}, {'name': 'artifact_form', 'kind': 'object', 'signature': ''}, {'name': 'payload_2d', 'kind': 'object', 'signature': ''}, {'name': 'payload_3d', 'kind': 'object', 'signature': ''}, {'name': 'write_2d', 'kind': 'object', 'signature': ''}, {'name': 'write_3d', 'kind': 'object', 'signature': ''}, {'name': 'AreaLayer', 'kind': 'object', 'signature': ''}, {'name': 'Context', 'kind': 'object', 'signature': ''}, {'name': 'Field', 'kind': 'object', 'signature': ''}, {'name': 'MapSpec', 'kind': 'object', 'signature': ''}, {'name': 'Metric', 'kind': 'object', 'signature': ''}, {'name': 'Outline', 'kind': 'object', 'signature': ''}, {'name': 'Ranking', 'kind': 'object', 'signature': ''}]
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

