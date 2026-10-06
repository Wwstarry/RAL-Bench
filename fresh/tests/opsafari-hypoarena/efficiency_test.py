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


def test_repeated_import_lookup_is_bounded():
    start = time.perf_counter()
    module = load_module()
    for _ in range(2000):
        for spec in SYMBOLS[:8]:
            getattr(module, spec["name"])
    assert time.perf_counter() - start < 10.0

