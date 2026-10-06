import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = '_layouts'
MODULE_ROOT = 'src/fmsave'
SYMBOLS = [{'name': 'annotations', 'kind': 'object', 'signature': ''}, {'name': 'dataclass', 'kind': 'object', 'signature': ''}, {'name': 'Protocol', 'kind': 'object', 'signature': ''}, {'name': 'GameInfoLayout', 'kind': 'class', 'signature': 'class'}, {'name': 'SaveSummaryLayout', 'kind': 'class', 'signature': 'class'}, {'name': 'SummaryStringsLayout', 'kind': 'class', 'signature': 'class'}, {'name': 'HumansLayout', 'kind': 'class', 'signature': 'class'}, {'name': 'NamePoolLayout', 'kind': 'class', 'signature': 'class'}, {'name': 'ClubRecordLayout', 'kind': 'class', 'signature': 'class'}, {'name': 'TeamListLayout', 'kind': 'class', 'signature': 'class'}, {'name': 'ClubStatusLayout', 'kind': 'class', 'signature': 'class'}, {'name': 'FinanceChainLayout', 'kind': 'class', 'signature': 'class'}, {'name': 'SponsorChainLayout', 'kind': 'class', 'signature': 'class'}, {'name': 'FacilityByteLayout', 'kind': 'class', 'signature': 'class'}, {'name': 'PersonBlockLayout', 'kind': 'class', 'signature': 'class'}, {'name': 'PlayerRecordLayout', 'kind': 'class', 'signature': 'class'}]
CONSTANTS = {'SPAN_CARRY_OVER_BYTES': 65536, 'FALLBACK_BUILD': '26.3.2+2329565'}


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


def test_documented_field_status_values_are_repeatable():
    repo = Path(os.environ["RACB_REPO_ROOT"]).resolve()
    sys.path.insert(0, str(repo / "src"))
    import fmsave
    assert fmsave.field_status(fmsave.Player, "attributes.finishing") == "verified"
    assert fmsave.field_status(fmsave.Player, "contract.wage") == "unconfirmed"
    assert fmsave.field_status(fmsave.Player, "attributes.finishing") == "verified"

