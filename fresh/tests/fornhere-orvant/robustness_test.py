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


def test_unknown_alias_and_invalid_table_degrade_predictably(tmp_path):
    module = load_module()
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    module._eslemeler.cache_clear()
    assert module.kanonik("unknown", bad) == "unknown"
    assert module.adlar("unknown", bad) == ("unknown",)
    assert module.iz_yolu("unknown", bad) is None

