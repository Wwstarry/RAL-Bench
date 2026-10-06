import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'commerce_common.config'
MODULE_ROOT = 'commerce-common'
SYMBOLS = [{'name': 'BaseAgentConfig', 'kind': 'class', 'signature': 'class'}]
CONSTANTS = {'DEFAULT_MEMORY_MODEL': 'claude-haiku-4-5-20251001'}


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


def test_documented_agent_config_defaults_and_round_trip():
    cls = load_module().BaseAgentConfig
    config = cls(model="claude-test")
    assert config.brand_name == "the store"
    assert config.max_tool_iterations == 8
    assert config.enable_memory is True
    assert cls.model_validate(config.model_dump()) == config

