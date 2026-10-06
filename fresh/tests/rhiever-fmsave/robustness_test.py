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


def test_documented_unknown_field_raises_key_error():
    repo = Path(os.environ["RACB_REPO_ROOT"]).resolve()
    sys.path.insert(0, str(repo / "src"))
    import fmsave
    with pytest.raises(KeyError):
        fmsave.field_status(fmsave.Player, "not.a.real.field")

