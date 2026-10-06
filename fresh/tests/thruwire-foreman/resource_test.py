import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'foreman'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'FactoryConfig', 'kind': 'object', 'signature': ''}, {'name': 'Directive', 'kind': 'object', 'signature': ''}, {'name': 'FactoryAssessment', 'kind': 'object', 'signature': ''}, {'name': 'FactoryState', 'kind': 'object', 'signature': ''}, {'name': 'ForemanResult', 'kind': 'object', 'signature': ''}, {'name': 'InterventionType', 'kind': 'object', 'signature': ''}, {'name': 'Check', 'kind': 'object', 'signature': ''}, {'name': 'Responsibility', 'kind': 'object', 'signature': ''}, {'name': 'ResponsibilityRegistry', 'kind': 'object', 'signature': ''}, {'name': 'ResponsibilityRoute', 'kind': 'object', 'signature': ''}, {'name': 'configured_registry', 'kind': 'object', 'signature': ''}, {'name': 'GlobalResponsibilityRouter', 'kind': 'object', 'signature': ''}, {'name': 'JevResponsibilityRouter', 'kind': 'object', 'signature': ''}, {'name': 'RoutingDecision', 'kind': 'object', 'signature': ''}, {'name': 'FactoryRuntime', 'kind': 'object', 'signature': ''}]
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

