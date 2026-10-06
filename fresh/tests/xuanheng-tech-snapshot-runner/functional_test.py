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


def test_documented_cli_contract_has_exact_public_commands():
    # README.md, "Public interface and contract"; tool_cli_contract.json v3.
    import json

    repo = Path(os.environ["RACB_REPO_ROOT"]).resolve()
    contract = json.loads((repo / "tool_cli_contract.json").read_text(encoding="utf-8"))
    assert contract["contract_version"] == 3
    assert contract["command_invocation"] == "snapshot-runner <command>"
    assert contract["primary_command"]["subcommands"] == [
        "branch-review", "diff-audit", "read", "repo-status", "test-triage"
    ]

