import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'companion_state'
MODULE_ROOT = 'src/usagetrim/core'
SYMBOLS = [{'name': 'state_dir', 'kind': 'function', 'signature': '()'}, {'name': 'settings', 'kind': 'function', 'signature': '()'}, {'name': 'paused', 'kind': 'function', 'signature': '()'}, {'name': 'update_settings', 'kind': 'function', 'signature': '(**changes)'}, {'name': 'already_wrapped', 'kind': 'function', 'signature': '(command)'}, {'name': 'project_for', 'kind': 'function', 'signature': '(path)'}, {'name': 'client_name', 'kind': 'function', 'signature': '(default)'}]
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


def test_companion_settings_persist_merge_and_pause(tmp_path, monkeypatch):
    module = load_module()
    monkeypatch.setenv("USAGETRIM_STATE_DIR", str(tmp_path))
    assert module.settings() == {}
    assert module.update_settings(paused=True, client="codex") == {"paused": True, "client": "codex"}
    assert module.paused() is True
    assert module.update_settings(paused=False) == {"paused": False, "client": "codex"}
    assert module.paused() is False

