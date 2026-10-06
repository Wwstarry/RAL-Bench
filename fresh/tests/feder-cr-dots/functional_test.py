import importlib
import inspect
import os
import sys
import time
import types
from pathlib import Path

import pytest

MODULE = 'dots.cli'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'main', 'kind': 'function', 'signature': '(argv)'}]
CONSTANTS = {'SUBCOMMAND': 'ui'}


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


def test_documented_wrapper_forwards_every_argument_to_ui(monkeypatch):
    calls = []
    package = types.ModuleType("invisible_playwright_mcp")
    target = types.ModuleType("invisible_playwright_mcp.cli")
    target.main = lambda **kwargs: calls.append(kwargs)
    monkeypatch.setitem(sys.modules, "invisible_playwright_mcp", package)
    monkeypatch.setitem(sys.modules, "invisible_playwright_mcp.cli", target)
    load_module().main(["--openrouter-key", "test-key", "--port", "8766"])
    assert calls == [{"args": ["ui", "--openrouter-key", "test-key", "--port", "8766"], "prog_name": "dots"}]

