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


def test_repeated_import_lookup_is_bounded():
    start = time.perf_counter()
    module = load_module()
    for _ in range(2000):
        for spec in SYMBOLS[:8]:
            getattr(module, spec["name"])
    assert time.perf_counter() - start < 10.0

