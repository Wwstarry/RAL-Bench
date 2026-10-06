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


def test_candidate_softmax_is_normalized_and_repeatable():
    module = load_module()
    values = module.candidate_softmax({"a": 1.0, "b": 2.0, "c": 3.0})
    assert len(values) == 3
    assert abs(sum(values.values()) - 1.0) < 1e-9
    assert values["c"] > values["b"] > values["a"]
    assert values == module.candidate_softmax({"a": 1.0, "b": 2.0, "c": 3.0})


def test_candidate_softmax_is_normalized_exact_and_repeatable():
    mod = load_module()
    result = mod.candidate_softmax({"yes": 0.0, "no": 0.0})
    assert result == {"yes": 0.5, "no": 0.5}
    assert mod.candidate_softmax({"yes": 0.0, "no": 0.0}) == result


def test_documented_boolean_schema_compiles_to_two_choices():
    decision = load_module().compile_json_schema(
        {"type": "object", "properties": {"approved": {"type": "boolean"}}, "required": ["approved"]}
    )[0]
    assert decision.name == "approved"
    assert decision.choices == (True, False)

