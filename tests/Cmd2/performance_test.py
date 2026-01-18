from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Optional

import io

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("CMD2_TARGET", "generated").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "cmd2"
else:
    REPO_ROOT = ROOT / "generation" / "cmd2"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cmd2 import Cmd, Statement  # type: ignore  # noqa: E402


class PerfApp(Cmd):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__()
        self.prompt = ""

    def do_ping(self, _: Statement) -> None:
        self.poutput("pong")


def run_commands(app: PerfApp, commands: list[str]) -> str:
    buffer = io.StringIO()
    saved_stdout = app.stdout
    app.stdout = buffer
    try:
        app.runcmds_plus_hooks(commands)
    finally:
        app.stdout = saved_stdout
    return buffer.getvalue()


def test_bulk_commands_performance() -> None:
    app = PerfApp()
    commands = ["ping"] * 2000

    start = time.perf_counter()
    output = run_commands(app, commands)
    elapsed = time.perf_counter() - start

    # Make sure all commands ran
    assert output.count("pong") == len(commands)

    # No strict upper bound here; the absolute value will be used
    # as a baseline reference in the benchmark configuration.
    assert elapsed >= 0.0
