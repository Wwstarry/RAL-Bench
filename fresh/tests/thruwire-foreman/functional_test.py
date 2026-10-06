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


def test_public_module_imports():
    assert load_module().__name__ == MODULE


@pytest.mark.parametrize("spec", SYMBOLS)
def test_declared_public_symbol(spec):
    value = getattr(load_module(), spec["name"])
    if spec["kind"] == "class":
        assert inspect.isclass(value)
    elif spec["kind"] == "function":
        assert callable(value)
    else:
        assert value is not None


@pytest.mark.parametrize("name, expected", list(CONSTANTS.items()))
def test_public_literal_constant(name, expected):
    assert getattr(load_module(), name) == expected


def test_documented_factory_config_defaults_and_round_trip():
    mod = load_module()
    config = mod.FactoryConfig()
    assert config.max_concurrent_workers == 1
    assert config.max_workers == 3
    assert config.max_iterations == 20
    assert mod.FactoryConfig.model_validate(config.model_dump()) == config


def test_factory_state_has_initial_created_state():
    mod = load_module()
    state = mod.FactoryState(run_id="run-1", job="Fix the parser", repository="/repo")
    assert state.status.value == "CREATED"
    assert state.iteration == 0
    assert state.workers == []

