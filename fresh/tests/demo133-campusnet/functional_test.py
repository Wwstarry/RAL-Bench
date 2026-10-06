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


def test_config_roundtrip_and_environment_precedence(tmp_path, monkeypatch):
    module = load_module()
    path = tmp_path / "config.json"
    config = module.Config(username="file-user", provider="drcom", timeout=12, path=str(path))
    assert config.save(include_password=False) == str(path)
    monkeypatch.setenv("CAMPUSNET_USERNAME", "env-user")
    loaded = module.load_config(str(path))
    assert loaded.username == "env-user"
    assert loaded.provider == "drcom"
    assert loaded.timeout == 12
    assert "password" not in loaded.to_dict()

