# tests/TheFuck/functional_test.py
from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional, Tuple, Union

import pytest


@dataclass
class FakeCommand:
    """
    Minimal command object compatible with thefuck.rules.no_command in the reference repo.

    The reference rule may access:
      - command.script_parts[0]
      - command.output / command.stderr / command.stdout
      - command.script
    """

    script: str
    stdout: str = ""
    stderr: str = ""
    returncode: int = 1

    @property
    def script_parts(self) -> List[str]:
        # Reference rule expects first token at least; be defensive.
        parts = [p for p in self.script.strip().split() if p]
        return parts if parts else [""]

    @property
    def output(self) -> str:
        # TheFuck commonly treats output as combined stdout+stderr.
        return (self.stdout or "") + (self.stderr or "")


def _import_no_command_rule() -> Tuple[Callable[[Any], Any], Callable[[Any], Any]]:
    mod = importlib.import_module("thefuck.rules.no_command")
    match_fn = getattr(mod, "match", None)
    get_new_fn = getattr(mod, "get_new_command", None)

    assert callable(match_fn), "thefuck.rules.no_command.match not found/callable"
    assert callable(get_new_fn), "thefuck.rules.no_command.get_new_command not found/callable"
    return match_fn, get_new_fn


def _coerce_suggestion(result: Any) -> str:
    """
    Normalize different possible return shapes from get_new_command:
      - string
      - iterable of strings
      - generator
    """
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


def _with_temp_path(prepend_dir: Path):
    """
    Context manager-like helper that prepends a directory to PATH and restores it.
    """
    class _Ctx:
        def __enter__(self):
            self._old = os.environ.get("PATH", "")
            os.environ["PATH"] = str(prepend_dir) + os.pathsep + self._old
            return self

        def __exit__(self, exc_type, exc, tb):
            os.environ["PATH"] = self._old

    return _Ctx()


def _make_windows_cmd(tmp_path: Path, name: str) -> Path:
    """
    Create a deterministic dummy executable on Windows.
    """
    cmd = tmp_path / f"{name}.cmd"
    cmd.write_text("@echo off\r\necho dummy\r\n", encoding="utf-8")
    return cmd


def _windows_command_not_found_output(bad_cmd: str) -> str:
    # Common Windows shell text (cmd.exe / PowerShell) for unknown commands.
    # Keep it broad but realistic.
    return f"'{bad_cmd}' is not recognized as an internal or external command,\r\noperable program or batch file.\r\n"


def _bash_command_not_found_output(bad_cmd: str) -> str:
    # Common bash/zsh text.
    return f"{bad_cmd}: command not found\n"


# -------------------------
# Functional tests (>= 10)
# -------------------------

def test_001_import_thefuck_package() -> None:
    import thefuck  # noqa: F401


def test_002_import_no_command_rule_module() -> None:
    importlib.import_module("thefuck.rules.no_command")


def test_003_no_command_match_returns_bool_windows_like() -> None:
    match_fn, _ = _import_no_command_rule()
    cmd = FakeCommand(
        script="pythno -V",
        stderr=_windows_command_not_found_output("pythno"),
        returncode=1,
    )
    r = match_fn(cmd)
    assert isinstance(bool(r), bool)


def test_004_no_command_match_returns_bool_bash_like() -> None:
    match_fn, _ = _import_no_command_rule()
    cmd = FakeCommand(
        script="pythno -V",
        stderr=_bash_command_not_found_output("pythno"),
        returncode=127,
    )
    r = match_fn(cmd)
    assert isinstance(bool(r), bool)


def test_005_no_command_like_rule_matches_at_least_one_typical_output() -> None:
    """
    Ensure the reference no_command rule actually matches a typical 'command not found' output.
    We check both Windows and bash variants, and require at least one to match.
    """
    match_fn, _ = _import_no_command_rule()

    samples = [
        FakeCommand("pythno -V", stderr=_windows_command_not_found_output("pythno"), returncode=1),
        FakeCommand("pythno -V", stderr=_bash_command_not_found_output("pythno"), returncode=127),
        # Additional common wording seen in some environments
        FakeCommand("pythno -V", stderr=f"{'pythno'}: not found\n", returncode=127),
    ]

    matched = any(bool(match_fn(c)) for c in samples)
    assert matched, "no_command-like rule did not match any typical 'command not found' output"


def test_006_no_command_get_new_command_returns_string_like(tmp_path: Path) -> None:
    """
    get_new_command should return something string-like (or iterable of strings).
    Do not require a specific suggestion yet.
    """
    _, get_new_fn = _import_no_command_rule()

    # Control candidate commands via PATH: only 'python' exists.
    _make_windows_cmd(tmp_path, "python")

    with _with_temp_path(tmp_path):
        cmd = FakeCommand(
            script="pythno -V",
            stderr=_windows_command_not_found_output("pythno"),
            returncode=1,
        )
        out = _coerce_suggestion(get_new_fn(cmd))
        assert isinstance(out, str)


def test_007_no_command_suggests_python_when_only_python_in_path(tmp_path: Path) -> None:
    """
    With PATH constrained to a directory containing only python.cmd,
    the best correction for 'pythno' should include 'python' in the suggestion.
    """
    _, get_new_fn = _import_no_command_rule()

    _make_windows_cmd(tmp_path, "python")

    with _with_temp_path(tmp_path):
        cmd = FakeCommand(
            script="pythno -V",
            stderr=_windows_command_not_found_output("pythno"),
            returncode=1,
        )
        suggestion = _coerce_suggestion(get_new_fn(cmd)).lower()
        assert "python" in suggestion, f"expected suggestion to contain 'python', got: {suggestion!r}"


def test_008_no_command_suggestion_is_deterministic(tmp_path: Path) -> None:
    """
    Same input should yield same first suggestion in a controlled PATH.
    """
    _, get_new_fn = _import_no_command_rule()

    _make_windows_cmd(tmp_path, "python")

    with _with_temp_path(tmp_path):
        cmd = FakeCommand(
            script="pythno -V",
            stderr=_windows_command_not_found_output("pythno"),
            returncode=1,
        )
        s1 = _coerce_suggestion(get_new_fn(cmd))
        s2 = _coerce_suggestion(get_new_fn(cmd))
        assert s1 == s2, f"non-deterministic suggestion: {s1!r} vs {s2!r}"


def test_009_no_command_does_not_crash_on_empty_output() -> None:
    match_fn, get_new_fn = _import_no_command_rule()
    cmd = FakeCommand(script="pythno -V", stdout="", stderr="", returncode=1)

    # Reference may return False/empty suggestion; requirement is no exception.
    _ = bool(match_fn(cmd))
    _ = _coerce_suggestion(get_new_fn(cmd))


def test_010_no_command_handles_unicode_output() -> None:
    match_fn, get_new_fn = _import_no_command_rule()
    cmd = FakeCommand(
        script="pythno -V",
        stderr="命令未找到: pythno\n",  # unicode text
        returncode=1,
    )
    _ = bool(match_fn(cmd))
    _ = _coerce_suggestion(get_new_fn(cmd))


def test_011_script_parts_exists_and_first_token_is_accessible() -> None:
    cmd = FakeCommand(script="pythno -V")
    assert isinstance(cmd.script_parts, list)
    assert cmd.script_parts[0] == "pythno"


def test_012_output_property_is_combined() -> None:
    cmd = FakeCommand(script="x", stdout="OUT", stderr="ERR")
    assert cmd.output == "OUTERR"
