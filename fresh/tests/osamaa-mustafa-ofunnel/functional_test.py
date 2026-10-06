import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'ofunnel'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'ADAPTERS', 'kind': 'object', 'signature': ''}, {'name': 'capture', 'kind': 'object', 'signature': ''}, {'name': 'from_csv', 'kind': 'object', 'signature': ''}, {'name': 'from_html', 'kind': 'object', 'signature': ''}, {'name': 'from_json', 'kind': 'object', 'signature': ''}, {'name': 'from_text_kv', 'kind': 'object', 'signature': ''}, {'name': 'from_xml', 'kind': 'object', 'signature': ''}, {'name': 'sniff', 'kind': 'object', 'signature': ''}, {'name': 'by_construct', 'kind': 'object', 'signature': ''}, {'name': 'collections', 'kind': 'object', 'signature': ''}, {'name': 'fields', 'kind': 'object', 'signature': ''}, {'name': 'normalize', 'kind': 'object', 'signature': ''}, {'name': 'records', 'kind': 'object', 'signature': ''}, {'name': 'ANNOTATION', 'kind': 'object', 'signature': ''}, {'name': 'BOOLEAN', 'kind': 'object', 'signature': ''}, {'name': 'COLLECTION', 'kind': 'object', 'signature': ''}]
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


def test_documented_lossless_json_capture_and_typed_fields():
    # README.md, "Lossless capture into one language".
    module = load_module()
    raw = b'{"name":"Ada","active":true,"n":3}'
    node, fmt = module.capture(raw)
    assert fmt == "json"
    assert module.check_complete(raw, node, fmt) is True
    assert [(item.key, item.value, item.vtype) for item in module.fields(node)] == [
        ("name", "Ada", "string"),
        ("active", "true", "boolean"),
        ("n", "3", "number"),
    ]

