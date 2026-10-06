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


def test_public_surface_is_finite():
    module = load_module()
    names = dir(module)
    assert MODULE.split(".")[-1] in module.__name__
    assert len(names) < 10000

