import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'context_eval'
MODULE_ROOT = 'bench'
SYMBOLS = [{'name': 'build', 'kind': 'function', 'signature': '()'}, {'name': 'fixture', 'kind': 'function', 'signature': '(folder)'}, {'name': 'score', 'kind': 'function', 'signature': '(scores, records, metrics, lines)'}]
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


def test_documented_plain_text_question_is_exact_and_repeatable():
    sys.path.insert(0, str(Path(os.environ["RACB_REPO_ROOT"]) / "src"))
    cli = importlib.import_module("jgrep.cli")
    expected = 'The text fits this description: "a complaint about noise"'
    assert cli.question("a complaint about noise").instructions == expected
    assert cli.question("a complaint about noise").instructions == expected


def test_documented_diff_question_preserves_change_semantics():
    sys.path.insert(0, str(Path(os.environ["RACB_REPO_ROOT"]) / "src"))
    instructions = importlib.import_module("jgrep.cli").question(
        "removes error handling", diff=True
    ).instructions
    assert "Compare the before and after code together" in instructions
    assert "Judge the change" in instructions

