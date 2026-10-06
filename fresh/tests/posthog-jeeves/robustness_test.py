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


def test_documented_request_boundaries_fail_closed():
    module = load_module()
    from inference.types import Options
    with pytest.raises(ValueError, match="state is required"):
        module.parse_request({"questions": {"q": {"type": "noul"}}}, Options())
    with pytest.raises(ValueError, match="non-empty"):
        module.parse_request({"state": "x", "questions": {}}, Options())
    with pytest.raises(ValueError, match="1..255"):
        module.parse_question("q", {"type": "choice", "criteria": {}})
    with pytest.raises(ValueError, match="unknown options"):
        module.parse_options({"temperature": 1}, Options())

