# tests/TheFuck/robustness_test.py
from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Tuple

import pytest


@dataclass
class FakeCommand:
    script: str
    stdout: str = ""
    stderr: str = ""
    returncode: int = 1

    @property
    def script_parts(self) -> List[str]:
        parts = [p for p in self.script.strip().split() if p]
        return parts if parts else [""]

    @property
    def output(self) -> str:
        return (self.stdout or "") + (self.stderr or "")


def _import_no_command_rule() -> Tuple[Callable[[Any], Any], Callable[[Any], Any]]:
    mod = importlib.import_module("thefuck.rules.no_command")
    match_fn = getattr(mod, "match", None)
    get_new_fn = getattr(mod, "get_new_command", None)
    assert callable(match_fn)
    assert callable(get_new_fn)
    return match_fn, get_new_fn


def _coerce_suggestion(result: Any) -> str:
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    if isinstance(result, (list, tuple)):
        return str(result[0]) if result else ""
    if isinstance(result, Iterable):
        for x in result:
            return str(x)
        return ""
    return str(result)


def test_001_empty_output_does_not_crash_no_command_rule() -> None:
    match_fn, get_new_fn = _import_no_command_rule()
    cmd = FakeCommand(script="pythno -V", stdout="", stderr="", returncode=1)
    _ = bool(match_fn(cmd))
    _ = _coerce_suggestion(get_new_fn(cmd))


def test_002_very_long_output_does_not_crash() -> None:
    match_fn, get_new_fn = _import_no_command_rule()
    long_err = ("X" * 20000) + "\n"
    cmd = FakeCommand(script="pythno -V", stderr=long_err, returncode=1)
    _ = bool(match_fn(cmd))
    _ = _coerce_suggestion(get_new_fn(cmd))


def test_003_unicode_and_control_chars_do_not_crash() -> None:
    match_fn, get_new_fn = _import_no_command_rule()
    err = "命令未找到\x00\x1b[31m pythno \x1b[0m\n"
    cmd = FakeCommand(script="pythno -V", stderr=err, returncode=1)
    _ = bool(match_fn(cmd))
    _ = _coerce_suggestion(get_new_fn(cmd))


def test_004_empty_script_is_handled_defensively() -> None:
    match_fn, get_new_fn = _import_no_command_rule()
    cmd = FakeCommand(script="", stderr="command not found\n", returncode=127)
    _ = bool(match_fn(cmd))
    _ = _coerce_suggestion(get_new_fn(cmd))
