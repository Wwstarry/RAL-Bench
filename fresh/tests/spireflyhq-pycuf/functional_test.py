import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'pycuf'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'annotations', 'kind': 'object', 'signature': ''}, {'name': 'PackageNotFoundError', 'kind': 'object', 'signature': ''}, {'name': 'policy', 'kind': 'object', 'signature': ''}, {'name': 'Totals', 'kind': 'object', 'signature': ''}, {'name': 'ForbiddenConstructError', 'kind': 'object', 'signature': ''}, {'name': 'LimitExceededError', 'kind': 'object', 'signature': ''}, {'name': 'MissingExtraError', 'kind': 'object', 'signature': ''}, {'name': 'NotCufError', 'kind': 'object', 'signature': ''}, {'name': 'PycufError', 'kind': 'object', 'signature': ''}, {'name': 'XmlSyntaxError', 'kind': 'object', 'signature': ''}, {'name': 'CODES', 'kind': 'object', 'signature': ''}, {'name': 'Finding', 'kind': 'object', 'signature': ''}, {'name': 'Severity', 'kind': 'object', 'signature': ''}, {'name': 'Bundle', 'kind': 'object', 'signature': ''}, {'name': 'Costs', 'kind': 'object', 'signature': ''}, {'name': 'CostType', 'kind': 'object', 'signature': ''}]
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


def test_documented_zero_factor_policy_changes_exact_total():
    module = load_module()
    toy = b'''<?xml version="1.0" encoding="UTF-8"?>
<CUF AANMAAKDATUMTIJD="2026-10-01T10:15:00">
  <PROJECTGEGEVENS CUF_VERSIE="4.003" PROJECTNUMMER="1" PROJECTNAAM="Schuurtje"/>
  <BEGROTING><BEGROTINGSREGEL OMSCHRIJVING="metselwerk" HOEVEELHEID="10" HOEVEELHEID_FACTOR="0" MATERIAALPRIJS="50" BTW="21"/></BEGROTING>
</CUF>'''
    cuf = module.read(toy)
    assert cuf.totals().estimate.total == 500
    assert cuf.totals(policy="schema").estimate.total == 0
    assert cuf.totals().estimate.total == 500

