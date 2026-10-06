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


def test_public_surface_is_finite():
    module = load_module()
    names = dir(module)
    assert MODULE.split(".")[-1] in module.__name__
    assert len(names) < 10000

