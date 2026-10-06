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


def test_repeated_import_is_stable():
    first = load_module()
    assert importlib.import_module(MODULE) is first


def test_missing_public_name_raises_attribute_error():
    with pytest.raises(AttributeError):
        getattr(load_module(), "__ral_bench_missing_public_name__")


@pytest.mark.parametrize("spec", SYMBOLS)
def test_public_callables_are_introspectable(spec):
    value = getattr(load_module(), spec["name"])
    if spec["kind"] in {"function", "class"}:
        inspect.signature(value)


def test_typed_runtime_bounds_reject_invalid_values():
    mod = load_module()
    with pytest.raises(Exception):
        mod.FactoryConfig(max_workers=0)
    with pytest.raises(Exception):
        mod.FactoryConfig(periodic_assessment_seconds=0)
    with pytest.raises(Exception):
        mod.FactoryState(run_id="", job="work", repository="/repo")

