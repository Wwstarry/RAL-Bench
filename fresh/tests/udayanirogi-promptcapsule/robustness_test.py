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


def test_documented_corruption_and_signature_fail_closed():
    module = load_module()
    capsule = module.pack("Summarise the Q3 report", sign="shared-secret")
    assert module.unpack(capsule, verify_signature="shared-secret") == "Summarise the Q3 report"
    with pytest.raises(module.SignatureError):
        module.unpack(capsule, verify_signature="wrong-secret")
    corrupted = module.pack("payload")[:-1] + "!"
    with pytest.raises(module.PromptCapsuleError):
        module.unpack(corrupted)

