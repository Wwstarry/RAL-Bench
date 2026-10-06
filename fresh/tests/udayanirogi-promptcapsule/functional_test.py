import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'promptcapsule'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'GitHubGistBackend', 'kind': 'object', 'signature': ''}, {'name': 'InMemoryBackend', 'kind': 'object', 'signature': ''}, {'name': 'S3Backend', 'kind': 'object', 'signature': ''}, {'name': 'SQLiteBackend', 'kind': 'object', 'signature': ''}, {'name': 'CapsuleResult', 'kind': 'object', 'signature': ''}, {'name': 'PromptCapsule', 'kind': 'object', 'signature': ''}, {'name': 'FormatError', 'kind': 'object', 'signature': ''}, {'name': 'IntegrityError', 'kind': 'object', 'signature': ''}, {'name': 'PromptCapsuleError', 'kind': 'object', 'signature': ''}, {'name': 'SignatureError', 'kind': 'object', 'signature': ''}, {'name': 'SizeLimitError', 'kind': 'object', 'signature': ''}, {'name': 'VaultError', 'kind': 'object', 'signature': ''}, {'name': 'IntegrityChecker', 'kind': 'object', 'signature': ''}, {'name': 'default_vault_path', 'kind': 'object', 'signature': ''}, {'name': 'pack', 'kind': 'object', 'signature': ''}, {'name': 'unpack', 'kind': 'object', 'signature': ''}]
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


def test_documented_pack_round_trip_is_exact_and_repeatable():
    module = load_module()
    text = "You are a helpful Python coding assistant.\nUnicode: 测试"
    first = module.pack(text)
    second = module.pack(text)
    assert isinstance(first, str) and first.startswith("cap_i_")
    assert module.unpack(first) == text
    assert module.unpack(second) == text

