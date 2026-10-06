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


def test_documented_graph_round_trip_and_reusable_state():
    rdf = load_module()
    graph = rdf.Graph()
    triple = (rdf.URIRef("urn:alice"), rdf.URIRef("urn:name"), rdf.Literal("Alice"))
    graph.add(triple)
    graph.add(triple)
    assert len(graph) == 1
    assert list(graph.objects(triple[0], triple[1])) == [triple[2]]
    encoded = graph.serialize(format="nt")
    restored = rdf.Graph().parse(data=encoded, format="nt")
    assert set(restored) == {triple}

