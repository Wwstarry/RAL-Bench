import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'inference.api'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'parse_options', 'kind': 'function', 'signature': '(raw, defaults)'}, {'name': 'parse_question', 'kind': 'function', 'signature': '(qid, raw)'}, {'name': 'parse_request', 'kind': 'function', 'signature': '(body, defaults)'}, {'name': 'r2', 'kind': 'function', 'signature': '(x)'}, {'name': 'choice_confidence', 'kind': 'function', 'signature': '(p)'}, {'name': 'score_confidence', 'kind': 'function', 'signature': '(p)'}, {'name': 'answer', 'kind': 'function', 'signature': '(q, p)'}, {'name': 'response', 'kind': 'function', 'signature': '(record, model, opts, results, tok, latency_ms)'}]
CONSTANTS = {'MAX_OPTIONS': 255, 'MODEL_ID': 'jeeves-latest'}


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


def test_documented_jev_request_is_parsed_exactly():
    module = load_module()
    from inference.types import Options
    body = {
        "state": "I was charged twice.",
        "questions": {
            "billing": {"type": "noul", "instructions": "Is this about billing?"},
            "tone": {"type": "choice", "instructions": "Tone?", "criteria": {"calm": None, "angry": None}},
            "urgency": {"type": "score", "instructions": "Urgency?", "criteria": ["wait", "today"]},
        },
        "options": {"think": False, "max_think": 512},
    }
    record, model, options = module.parse_request(body, Options())
    assert model == "jeeves-latest"
    assert [question.id for question in record.questions] == ["billing", "tone", "urgency"]
    assert options.think is False and options.max_think == 512
    assert module.answer(record.questions[1], [0.25, 0.75]) == {
        "type": "choice", "choice": "angry", "confidence": 0.5,
        "probabilities": {"calm": 0.25, "angry": 0.75},
    }

