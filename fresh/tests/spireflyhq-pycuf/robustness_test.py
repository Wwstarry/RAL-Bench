import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'pycuf'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'annotations', 'kind': 'object', 'signature': ''}, {'name': 'PackageNotFoundError', 'kind': 'object', 'signature': ''}, {'name': 'policy', 'kind': 'object', 'signature': ''}, {'name': 'Totals', 'kind': 'object', 'signature': ''}, {'name': 'ForbiddenConstructError', 'kind': 'object', 'signature': ''}, {'name': 'LimitExceededError', 'kind': 'object', 'signature': ''}, {'name': 'MissingExtraError', 'kind': 'object', 'signature': ''}, {'name': 'NotCufError', 'kind': 'object', 'signature': ''}, {'name': 'PycufError', 'kind': 'object', 'signature': ''}, {'name': 'XmlSyntaxError', 'kind': 'object', 'signature': ''}, {'name': 'CODES', 'kind': 'object', 'signature': ''}, {'name': 'Finding', 'kind': 'object', 'signature': ''}, {'name': 'Severity', 'kind': 'object', 'signature': ''}, {'name': 'Bundle', 'kind': 'object', 'signature': ''}, {'name': 'Costs', 'kind': 'object', 'signature': ''}, {'name': 'CostType', 'kind': 'object', 'signature': ''}]
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


def test_invalid_policy_and_malformed_xml_are_rejected():
    module = load_module()
    with pytest.raises((ValueError, KeyError)):
        module.policy.resolve_policy("not-a-policy")
    with pytest.raises(module.PycufError):
        module.read(b"<CUF>")

