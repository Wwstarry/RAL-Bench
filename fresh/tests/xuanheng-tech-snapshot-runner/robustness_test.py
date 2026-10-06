import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'snapshot_runner.artifact'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'active_repository_root', 'kind': 'function', 'signature': '(repository_root)'}, {'name': 'SnapshotArtifact', 'kind': 'class', 'signature': 'class'}, {'name': 'snapshot_output_root', 'kind': 'function', 'signature': '(target_repo)'}]
CONSTANTS = {'SNAPSHOT_PUBLISH_DURABILITY_ERROR': 'snapshot published but snapshot-store durability sync failed', 'STATE_HOME_MISSING_ERROR': 'state home must already exist as a private directory', 'SNAPSHOT_META_SCHEMA_VERSION': 2, 'SUMMARY_SCHEMA_VERSION': 2, 'EVIDENCE_SCHEMA_VERSION': 1, 'SUMMARY_TEXT_LIMIT': 256, 'SUMMARY_WARNING_LIMIT': 5}


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


def test_documented_schema_and_summary_bounds_are_frozen():
    # README.md, "Public interface and contract" and "Artifacts and determinism".
    module = load_module()
    assert module.SNAPSHOT_META_SCHEMA_VERSION == 2
    assert module.SUMMARY_SCHEMA_VERSION == 2
    assert module.EVIDENCE_SCHEMA_VERSION == 1
    assert module.SUMMARY_TEXT_LIMIT == 256
    assert module.SUMMARY_WARNING_LIMIT == 5

