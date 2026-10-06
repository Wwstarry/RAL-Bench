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


def test_declared_json_capture_is_lossless_or_loud():
    # README.md, "Lossless or loud": malformed declared formats must fail.
    with pytest.raises(Exception):
        load_module().capture(b'{"unfinished":', fmt="json")

