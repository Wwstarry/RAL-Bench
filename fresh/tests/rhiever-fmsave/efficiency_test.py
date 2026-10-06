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


def test_repeated_import_lookup_is_bounded():
    start = time.perf_counter()
    module = load_module()
    for _ in range(2000):
        for spec in SYMBOLS[:8]:
            getattr(module, spec["name"])
    assert time.perf_counter() - start < 10.0

