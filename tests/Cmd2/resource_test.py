from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Optional

import io
import psutil

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


class ResourceApp(Cmd):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__()
        self.prompt = ""

    def do_noop(self, _: Statement) -> None:
        # Intentionally minimal work
        self.poutput("")
        

def run_commands(app: ResourceApp, commands: list[str]) -> str:
    buffer = io.StringIO()
    saved_stdout = app.stdout
    app.stdout = buffer
    try:
        app.runcmds_plus_hooks(commands)
    finally:
        app.stdout = saved_stdout
    return buffer.getvalue()


def test_memory_usage_for_many_commands() -> None:
    app = ResourceApp()
    commands = ["noop"] * 3000

    process = psutil.Process()
    base_mem = process.memory_info().rss

    run_commands(app, commands)

    # Let the process settle a bit before measuring
    time.sleep(0.5)
    used_mem = process.memory_info().rss - base_mem

    # Use a generous upper bound; the exact baseline value will be
    # recorded from the reference implementation.
    assert used_mem < 300 * 1024 * 1024  # 300 MB
