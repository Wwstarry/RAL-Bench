import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'typellm'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'benchmark_prefix_cache', 'kind': 'object', 'signature': ''}, {'name': 'Choice', 'kind': 'object', 'signature': ''}, {'name': 'Generation', 'kind': 'object', 'signature': ''}, {'name': 'TypeLLMClient', 'kind': 'object', 'signature': ''}, {'name': 'candidate_softmax', 'kind': 'object', 'signature': ''}, {'name': 'run_schema', 'kind': 'object', 'signature': ''}, {'name': 'MAX_ENUM_CHOICES', 'kind': 'object', 'signature': ''}, {'name': 'Decision', 'kind': 'object', 'signature': ''}, {'name': 'SchemaError', 'kind': 'object', 'signature': ''}, {'name': 'compile_json_schema', 'kind': 'object', 'signature': ''}, {'name': 'GenerationCancelled', 'kind': 'object', 'signature': ''}, {'name': 'GenerationTimeout', 'kind': 'object', 'signature': ''}, {'name': 'SGLangClient', 'kind': 'object', 'signature': ''}, {'name': 'SGLangError', 'kind': 'object', 'signature': ''}, {'name': 'Usage', 'kind': 'object', 'signature': ''}, {'name': 'extract_candidate_logprobs', 'kind': 'object', 'signature': ''}]
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


def test_candidate_softmax_rejects_empty_candidates():
    module = load_module()
    with pytest.raises((AttributeError, ValueError)):
        module.candidate_softmax([])


def test_schema_and_probability_boundaries_fail_explicitly():
    mod = load_module()
    with pytest.raises(Exception):
        mod.compile_json_schema({"type": "array"})
    with pytest.raises((ValueError, ZeroDivisionError)):
        mod.candidate_softmax({"yes": 0.0}, temperature=0)

