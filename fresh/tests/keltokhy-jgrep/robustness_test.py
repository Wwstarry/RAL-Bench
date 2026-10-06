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


def test_cli_parser_rejects_out_of_range_threshold():
    sys.path.insert(0, str(Path(os.environ["RACB_REPO_ROOT"]) / "src"))
    cli = importlib.import_module("jgrep.cli")
    import io
    err = io.StringIO()
    assert cli.main(["-p", "1.1", "description"], err=err) == 2
    assert "finite probability" in err.getvalue()

