import subprocess
import sys

import pytest

from thefuck.corrector import get_suggestions
from thefuck.rules import load_rules
from thefuck.types import Command
from thefuck.main import main


def test_imports_and_rules_deterministic():
    rules1 = load_rules()
    rules2 = load_rules()
    assert [r.name for r in rules1] == [r.name for r in rules2]
    assert len(rules1) >= 3


def test_unknown_command_typo_suggests_git_status():
    cmd = Command(
        script="bash",
        command="gti status",
        stdout="",
        stderr="gti: command not found",
        return_code=127,
    )
    sugs = get_suggestions(cmd, load_rules())
    assert sugs and sugs[0] == "git status"


def test_wrong_git_subcommand():
    cmd = Command(
        script="bash",
        command="git ststus",
        stdout="",
        stderr="git: 'ststus' is not a git command. See 'git --help'.",
        return_code=1,
    )
    sugs = get_suggestions(cmd, load_rules())
    assert sugs[:1] == ["git status"]


def test_wrong_pip_subcommand_preserves_python_m_pip_shape():
    cmd = Command(
        script="bash",
        command="python -m pip instal requests",
        stdout="",
        stderr="ERROR: No such command 'instal'.",
        return_code=2,
    )
    sugs = get_suggestions(cmd, load_rules())
    assert sugs and sugs[0].startswith("python -m pip install")


def test_missing_cd_argument_suggests_home():
    cmd = Command(
        script="bash",
        command="cd",
        stdout="",
        stderr="cd: missing operand",
        return_code=1,
    )
    sugs = get_suggestions(cmd, load_rules())
    assert sugs[:1] == ["cd ~"]


def test_determinism_and_dedup():
    cmd = Command(
        script="bash",
        command="gti status",
        stdout="",
        stderr="gti: command not found",
        return_code=127,
    )
    r = load_rules()
    a = get_suggestions(cmd, r)
    b = get_suggestions(cmd, r)
    assert a == b
    assert len(a) == len(set(a))


def test_main_best_prints_only_suggestion_and_returns_0(capsys):
    rc = main(["--command", "gti status", "--stderr", "gti: command not found", "--exit-code", "127", "--best"])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.strip() == "git status"


def test_main_returns_1_when_previous_succeeded(capsys):
    rc = main(["--command", "echo ok", "--stdout", "ok", "--stderr", "", "--exit-code", "0", "--best"])
    out = capsys.readouterr().out
    assert rc == 1
    assert out.strip() == ""


def test_python_m_thefuck_version_smoke():
    proc = subprocess.run(
        [sys.executable, "-m", "thefuck", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() != ""