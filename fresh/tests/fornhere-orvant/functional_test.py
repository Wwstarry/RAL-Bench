import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'orvant_gelisim.projeler'
MODULE_ROOT = 'engine'
SYMBOLS = [{'name': 'kanonik', 'kind': 'function', 'signature': '(ad, yol)'}, {'name': 'adlar', 'kind': 'function', 'signature': '(ad, yol)'}, {'name': 'iz_yolu', 'kind': 'function', 'signature': '(ad, yol)'}]
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


def test_project_aliases_and_trace_path_from_public_table(tmp_path):
    module = load_module()
    table = tmp_path / "projects.json"
    table.write_text(
        '{"projeler":{"alpha":{"takma_adlar":["a","first"],"iz":"traces/alpha"}}}',
        encoding="utf-8",
    )
    module._eslemeler.cache_clear()
    assert module.kanonik("a", table) == "alpha"
    assert module.adlar("first", table) == ("alpha", "a", "first")
    assert module.iz_yolu("a", table) == "traces/alpha"

