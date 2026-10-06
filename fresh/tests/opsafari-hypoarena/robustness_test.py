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


def test_agent_request_rejects_unknown_task_and_blank_prompt():
    module = load_module()
    with pytest.raises(Exception):
        module.AgentRequest(task="unknown", prompt="x")
    with pytest.raises(Exception):
        module.AgentRequest(task="propose", prompt=" ")


def test_quality_and_request_boundaries_are_rejected():
    mod = load_module()
    with pytest.raises(Exception):
        mod.quality_tier(-0.01)
    with pytest.raises(Exception):
        mod.quality_tier(1.01)
    with pytest.raises(Exception):
        mod.AgentRequest(task="unknown", prompt="x")

