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


def test_public_surface_is_finite():
    module = load_module()
    names = dir(module)
    assert MODULE.split(".")[-1] in module.__name__
    assert len(names) < 10000

