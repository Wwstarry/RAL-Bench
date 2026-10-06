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


def test_documented_email_helpers_have_exact_repeatable_output():
    laya = load_module()
    body = "Hello team,\n\nPlease refund invoice 42.\n\nSent from my iPhone"
    assert laya.clean_email_body(body) == "Hello team,\n\nPlease refund invoice 42."
    expected = {"subject": "Duplicate bill", "body": "Please refund invoice 42.", "from": "a@example.test"}
    assert laya.email_state("Duplicate bill", "Please refund invoice 42.", "a@example.test") == expected
    assert laya.email_state("Duplicate bill", "Please refund invoice 42.", "a@example.test") == expected


def test_documented_script_detection():
    laya = load_module()
    assert laya.detect_script("plain English text") == "latin"
    assert laya.detect_script("日本語の文") == "han"

