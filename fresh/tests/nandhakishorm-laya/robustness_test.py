import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'laya'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'clean_email_body', 'kind': 'object', 'signature': ''}, {'name': 'email_state', 'kind': 'object', 'signature': ''}, {'name': 'AsyncHook', 'kind': 'object', 'signature': ''}, {'name': 'BaseHook', 'kind': 'object', 'signature': ''}, {'name': 'Hook', 'kind': 'object', 'signature': ''}, {'name': 'PredictContext', 'kind': 'object', 'signature': ''}, {'name': 'PredictHook', 'kind': 'object', 'signature': ''}, {'name': 'detect_language', 'kind': 'object', 'signature': ''}, {'name': 'detect_script', 'kind': 'object', 'signature': ''}, {'name': 'is_english', 'kind': 'object', 'signature': ''}, {'name': 'email_questions', 'kind': 'object', 'signature': ''}, {'name': 'guard_questions', 'kind': 'object', 'signature': ''}, {'name': 'moderation_questions', 'kind': 'object', 'signature': ''}, {'name': 'router_questions', 'kind': 'object', 'signature': ''}, {'name': 'triage_questions', 'kind': 'object', 'signature': ''}, {'name': 'DEFAULT_MODELS', 'kind': 'object', 'signature': ''}]
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


def test_email_helpers_reject_wrong_types_and_bound_output():
    laya = load_module()
    assert laya.clean_email_body(None) == ""
    assert len(laya.clean_email_body("x" * 20, max_chars=7)) <= 7
    assert laya.is_english(None) is True

