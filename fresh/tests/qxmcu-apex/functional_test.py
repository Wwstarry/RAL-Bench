import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'apex'
MODULE_ROOT = 'apex-py'
SYMBOLS = [{'name': 'Any', 'kind': 'object', 'signature': ''}, {'name': 'Dict', 'kind': 'object', 'signature': ''}, {'name': 'List', 'kind': 'object', 'signature': ''}, {'name': 'Optional', 'kind': 'object', 'signature': ''}, {'name': 'Union', 'kind': 'object', 'signature': ''}, {'name': 'DEFAULT_BLOCK_SIZE', 'kind': 'object', 'signature': ''}, {'name': 'FLAG_ENCRYPTED', 'kind': 'object', 'signature': ''}, {'name': 'FLAG_RECOVERY', 'kind': 'object', 'signature': ''}, {'name': 'ArchiveManifest', 'kind': 'object', 'signature': ''}, {'name': 'compress_archive', 'kind': 'object', 'signature': ''}, {'name': 'decompress_archive', 'kind': 'object', 'signature': ''}, {'name': 'read_archive_header', 'kind': 'object', 'signature': ''}, {'name': 'repair_archive', 'kind': 'object', 'signature': ''}, {'name': 'test_archive', 'kind': 'object', 'signature': ''}, {'name': 'analyze_file', 'kind': 'object', 'signature': ''}, {'name': 'run_benchmark', 'kind': 'object', 'signature': ''}]
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


def test_entropy_analysis_documented_profiles():
    load_module()
    from apex.analyzer import analyze_data

    empty = analyze_data(b"")
    assert (empty.total_bytes, empty.unique_bytes, empty.shannon_entropy) == (0, 0, 0.0)
    assert empty.classification == "Empty Data"
    text = analyze_data(b"hello world\n" * 20)
    assert text.total_bytes == 240
    assert text.classification == "Natural Text / Source Code / Structured Markup"
    assert 0.0 < text.shannon_entropy < 8.0

