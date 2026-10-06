import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'inference.api'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'parse_options', 'kind': 'function', 'signature': '(raw, defaults)'}, {'name': 'parse_question', 'kind': 'function', 'signature': '(qid, raw)'}, {'name': 'parse_request', 'kind': 'function', 'signature': '(body, defaults)'}, {'name': 'r2', 'kind': 'function', 'signature': '(x)'}, {'name': 'choice_confidence', 'kind': 'function', 'signature': '(p)'}, {'name': 'score_confidence', 'kind': 'function', 'signature': '(p)'}, {'name': 'answer', 'kind': 'function', 'signature': '(q, p)'}, {'name': 'response', 'kind': 'function', 'signature': '(record, model, opts, results, tok, latency_ms)'}]
CONSTANTS = {'MAX_OPTIONS': 255, 'MODEL_ID': 'jeeves-latest'}


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

