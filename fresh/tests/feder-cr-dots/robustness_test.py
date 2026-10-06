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


def test_wrapper_does_not_mutate_caller_arguments(monkeypatch):
    package = types.ModuleType("invisible_playwright_mcp")
    target = types.ModuleType("invisible_playwright_mcp.cli")
    target.main = lambda **kwargs: None
    monkeypatch.setitem(sys.modules, "invisible_playwright_mcp", package)
    monkeypatch.setitem(sys.modules, "invisible_playwright_mcp.cli", target)
    argv = ["--help"]
    load_module().main(argv)
    assert argv == ["--help"]

