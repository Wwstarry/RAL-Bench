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


def test_repeated_import_lookup_is_bounded():
    start = time.perf_counter()
    module = load_module()
    for _ in range(2000):
        for spec in SYMBOLS[:8]:
            getattr(module, spec["name"])
    assert time.perf_counter() - start < 10.0

