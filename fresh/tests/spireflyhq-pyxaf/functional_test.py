import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'pyxaf'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'annotations', 'kind': 'object', 'signature': ''}, {'name': 'PackageNotFoundError', 'kind': 'object', 'signature': ''}, {'name': 'detect', 'kind': 'object', 'signature': ''}, {'name': 'EncryptedAuditfileError', 'kind': 'object', 'signature': ''}, {'name': 'ForbiddenConstructError', 'kind': 'object', 'signature': ''}, {'name': 'LimitExceededError', 'kind': 'object', 'signature': ''}, {'name': 'MissingExtraError', 'kind': 'object', 'signature': ''}, {'name': 'NotAnAuditfileError', 'kind': 'object', 'signature': ''}, {'name': 'PyxafError', 'kind': 'object', 'signature': ''}, {'name': 'XmlSyntaxError', 'kind': 'object', 'signature': ''}, {'name': 'CODES', 'kind': 'object', 'signature': ''}, {'name': 'Finding', 'kind': 'object', 'signature': ''}, {'name': 'Severity', 'kind': 'object', 'signature': ''}, {'name': 'Family', 'kind': 'object', 'signature': ''}, {'name': 'FormatInfo', 'kind': 'object', 'signature': ''}, {'name': 'NamespaceStatus', 'kind': 'object', 'signature': ''}]
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


def test_documented_xaf40_detection_is_exact_and_repeatable():
    module = load_module()
    namespace = "http://www.odb.belastingdienst.nl/Belastingdienst/BCPP/1.1/structures/XmlauditfileXAF_4.0"
    payload = f'<?xml version="1.0"?><auditfile xmlns="{namespace}"/>'.encode()
    first = module.detect(payload)
    second = module.detect(payload)
    assert str(first.version) == "4.0"
    assert str(first.namespace_status) == "official"
    assert first == second

