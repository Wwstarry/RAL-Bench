from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import List, Tuple

from .utils import normalize_newlines, strip_ansi


@dataclass
class _Interaction:
    command: str
    expected_output_lines: List[str]


def _parse_transcript(text: str, prompt: str) -> List[_Interaction]:
    text = normalize_newlines(text)
    lines = text.split("\n")

    interactions: List[_Interaction] = []
    cur_cmd: str | None = None
    cur_out: List[str] = []

    def flush() -> None:
        nonlocal cur_cmd, cur_out
        if cur_cmd is not None:
            interactions.append(_Interaction(command=cur_cmd, expected_output_lines=cur_out))
        cur_cmd = None
        cur_out = []

    for line in lines:
        # Ignore full-line comments
        if line.startswith("#"):
            continue

        if prompt and line.startswith(prompt):
            flush()
            cur_cmd = line[len(prompt) :]
            cur_out = []
        else:
            if cur_cmd is None:
                # Allow leading text/comments before first prompt; ignore
                if line.strip() == "":
                    continue
                # Otherwise treat as noise and ignore (keeps runner permissive)
                continue
            cur_out.append(line)

    flush()
    return interactions


def _unified_diff(expected: str, actual: str, fromfile: str = "expected", tofile: str = "actual") -> str:
    exp_lines = expected.splitlines(keepends=True)
    act_lines = actual.splitlines(keepends=True)
    diff = difflib.unified_diff(exp_lines, act_lines, fromfile=fromfile, tofile=tofile)
    return "".join(diff)


class Transcript:
    def __init__(self, path: str, *, encoding: str = "utf-8") -> None:
        self.path = path
        self.encoding = encoding

    def run(self, app) -> Tuple[bool, str]:
        with open(self.path, "r", encoding=self.encoding) as f:
            content = f.read()

        interactions = _parse_transcript(content, getattr(app, "prompt", ""))

        for idx, inter in enumerate(interactions, start=1):
            actual = app.run_script(inter.command + "\n", echo=False, stop_on_error=False)
            actual = strip_ansi(normalize_newlines(actual))
            expected = normalize_newlines("\n".join(inter.expected_output_lines))

            # cmd2's capture is typically exact including trailing newlines. Make comparison line-based.
            act_lines = actual.split("\n")
            exp_lines = expected.split("\n")

            # Normalize final empty line behavior: if both end with a trailing newline,
            # split produces last "" element. Keep as-is to preserve exactness.
            if act_lines != exp_lines:
                exp_text = "\n".join(exp_lines)
                act_text = "\n".join(act_lines)
                header = f"Transcript mismatch in {self.path} at interaction #{idx}\nCommand: {inter.command}\n"
                diff = _unified_diff(exp_text + "\n", act_text + "\n", fromfile="expected", tofile="actual")
                return False, header + diff

        return True, ""


def run_transcript(app, path: str, *, encoding: str = "utf-8") -> Tuple[bool, str]:
    return Transcript(path, encoding=encoding).run(app)