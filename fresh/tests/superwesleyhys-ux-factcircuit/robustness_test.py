import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'factcircuit'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'DEFAULT_CONFIG', 'kind': 'object', 'signature': ''}, {'name': 'EvidenceProvider', 'kind': 'object', 'signature': ''}, {'name': 'run_verification', 'kind': 'object', 'signature': ''}]
CONSTANTS = {}


class _Provider:
    def search(self, claim, round_number, intent, limit):
        return []


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


def test_invalid_claim_and_provider_failure_are_explicit():
    mod = load_module()
    with pytest.raises(Exception):
        mod.run_verification({}, _Provider())

    class BrokenProvider:
        def search(self, claim, round_number, intent, limit):
            raise RuntimeError("offline failure")

    result = mod.run_verification(
        {"id": "c1", "text": "claim", "as_of": "2026-09-05T12:00:00Z"}, BrokenProvider()
    )
    assert result["status"] == "unresolved"
    assert result["stop_reason"] == "provider_error"
    assert "offline failure" not in str(result)

