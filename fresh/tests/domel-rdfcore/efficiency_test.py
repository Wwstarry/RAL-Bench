import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'rdfcore'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'BadSyntax', 'kind': 'object', 'signature': ''}, {'name': 'CompValueException', 'kind': 'object', 'signature': ''}, {'name': 'Error', 'kind': 'object', 'signature': ''}, {'name': 'ModificationException', 'kind': 'object', 'signature': ''}, {'name': 'ObjectTypeError', 'kind': 'object', 'signature': ''}, {'name': 'ParserError', 'kind': 'object', 'signature': ''}, {'name': 'PluginException', 'kind': 'object', 'signature': ''}, {'name': 'StoreException', 'kind': 'object', 'signature': ''}, {'name': 'UniquenessError', 'kind': 'object', 'signature': ''}, {'name': 'BNode', 'kind': 'object', 'signature': ''}, {'name': 'Identifier', 'kind': 'object', 'signature': ''}, {'name': 'IdentifiedNode', 'kind': 'object', 'signature': ''}, {'name': 'Literal', 'kind': 'object', 'signature': ''}, {'name': 'Node', 'kind': 'object', 'signature': ''}, {'name': 'TripleTerm', 'kind': 'object', 'signature': ''}, {'name': 'URIRef', 'kind': 'object', 'signature': ''}]
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

