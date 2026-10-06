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


class _Provider:
    def search(self, claim, round_number, intent, limit):
        evidence = {
            "id": f"e{round_number}", "claim_id": claim["id"],
            "url": f"https://example.test/{round_number}",
            "publisher_group": f"publisher-{round_number}", "origin_id": f"origin-{round_number}",
            "published_at": "2026-09-05T10:00:00Z", "retrieved_at": "2026-09-05T11:00:00Z",
            "content": f"Source {round_number} reports: The library opens on September 6.",
            "quote": "The library opens on September 6.",
            "stance": "supports",
        }
        return [evidence][:limit]


def test_documented_verification_adapter_is_deterministic():
    mod = load_module()
    claim = {"id": "c1", "text": "The library opens on September 6.", "as_of": "2026-09-05T12:00:00Z"}
    first = mod.run_verification(claim, _Provider())
    second = mod.run_verification(claim, _Provider())
    assert first == second
    assert first["claim"] == claim
    assert first["status"] == "supported"
    assert first["independent_source_counts"]["supports"] == 2

