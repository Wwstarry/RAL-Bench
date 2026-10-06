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


def test_public_surface_is_finite():
    module = load_module()
    names = dir(module)
    assert MODULE.split(".")[-1] in module.__name__
    assert len(names) < 10000

