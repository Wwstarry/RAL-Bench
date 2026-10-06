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


def test_documented_parser_rejects_invalid_turtle():
    rdf = load_module()
    with pytest.raises(Exception):
        rdf.Graph().parse(data="@prefix broken", format="turtle")
    with pytest.raises(Exception, match="No plugin registered"):
        rdf.Graph().serialize(format="unknown-format")

