import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'hypoarena.agents'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'AgentRequest', 'kind': 'class', 'signature': 'class'}, {'name': 'AgentResponse', 'kind': 'class', 'signature': 'class'}, {'name': 'Usage', 'kind': 'class', 'signature': 'class'}, {'name': 'count_words', 'kind': 'function', 'signature': '(text)'}, {'name': 'DiscoveryAgent', 'kind': 'class', 'signature': 'class'}, {'name': 'BaseAgent', 'kind': 'class', 'signature': 'class'}, {'name': 'quality_tier', 'kind': 'function', 'signature': '(quality)'}, {'name': 'ScriptedAgent', 'kind': 'class', 'signature': 'class'}, {'name': 'ReplayEntry', 'kind': 'class', 'signature': 'class'}, {'name': 'ReplayAgent', 'kind': 'class', 'signature': 'class'}, {'name': 'TranscriptTurn', 'kind': 'class', 'signature': 'class'}, {'name': 'replay_transcript', 'kind': 'function', 'signature': '(agent, proposal_prompt, context, rounds)'}, {'name': 'transcript_statement', 'kind': 'function', 'signature': '(turns)'}, {'name': 'merge_usage', 'kind': 'function', 'signature': '(*usages)'}, {'name': 'usage_summary', 'kind': 'function', 'signature': '(agents)'}, {'name': 'RecordingAgent', 'kind': 'class', 'signature': 'class'}]
CONSTANTS = {'NO_PROGRESS_MARKER': '(unchanged)', 'FOCUSED_SUFFIX': ' when assayed in the same population', 'MECHANISTIC_SUFFIX': ' when assayed in the same population, quantified by dose response', 'VAGUE_PROPOSAL': 'an intervention is associated with an outcome'}


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


def test_documented_agent_request_fingerprint_and_word_count():
    module = load_module()
    request = module.AgentRequest(task="propose", prompt="Use the evidence", context=("one", "two"))
    assert request.with_id().request_id.startswith("req_")
    assert request.with_id().fingerprint() == request.with_id().fingerprint()
    assert module.count_words("one two\nthree") == 3


def test_documented_quality_tiers_and_word_count_are_exact():
    mod = load_module()
    assert [mod.quality_tier(value) for value in (0.0, 0.5, 1.0)] == ["vague", "focused", "mechanistic"]
    assert mod.count_words("alpha, beta! gamma") == 3
    assert mod.count_words("alpha, beta! gamma") == mod.count_words("alpha, beta! gamma")


def test_usage_merge_preserves_totals_and_task_counts():
    mod = load_module()
    merged = mod.merge_usage(
        mod.Usage(calls=1, prompt_tokens=2, completion_tokens=3, by_task={"propose": 1}),
        mod.Usage(calls=2, prompt_tokens=5, completion_tokens=7, by_task={"propose": 1, "revise": 1}),
    )
    assert (merged.calls, merged.prompt_tokens, merged.completion_tokens) == (3, 7, 10)
    assert merged.by_task == {"propose": 2, "revise": 1}

