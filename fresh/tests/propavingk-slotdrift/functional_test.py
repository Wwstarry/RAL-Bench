import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'slotdrift.cli'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'build_parser', 'kind': 'function', 'signature': '()'}, {'name': 'load', 'kind': 'function', 'signature': '(path)'}, {'name': 'main', 'kind': 'function', 'signature': '(argv)'}]
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


def test_cli_analyzes_documented_jsonl_shape(tmp_path, capsys):
    module = load_module()
    sample = tmp_path / "slots.jsonl"
    sample.write_text(
        '\n'.join([
            '{"slot": 10, "parent": 9, "blockhash": "a", "leader": "L1", "commitment": "finalized"}',
            '{"slot": 11, "parent": 10, "blockhash": "b", "leader": "L1", "commitment": "finalized"}',
        ]) + '\n', encoding="utf-8"
    )
    code = module.main(["analyze", str(sample), "--format", "json"])
    output = capsys.readouterr().out
    assert code == 0
    assert '"records": 2' in output
    assert '"missing": []' in output

