import contextlib
import io
import os
import re
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, TextIO


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def splitlines_preserve_trailing(text: str) -> List[str]:
    text = normalize_line_endings(text)
    if text == "":
        return []
    if text.endswith("\n"):
        return text[:-1].split("\n") + [""]
    return text.split("\n")


@contextlib.contextmanager
def redirect_stdout(target: TextIO):
    old = sys.stdout
    sys.stdout = target
    try:
        yield target
    finally:
        sys.stdout = old


@contextlib.contextmanager
def redirect_stderr(target: TextIO):
    old = sys.stderr
    sys.stderr = target
    try:
        yield target
    finally:
        sys.stderr = old


@contextlib.contextmanager
def capture_output(merge_stderr: bool = False):
    buf = io.StringIO()
    if merge_stderr:
        with redirect_stdout(buf), redirect_stderr(buf):
            yield buf
    else:
        with redirect_stdout(buf):
            yield buf


def is_blank_line(line: str) -> bool:
    return strip_ansi(line).strip() == ""


@dataclass
class TranscriptResult:
    matched: bool
    expected: List[str]
    got: List[str]
    message: str = ""


def _read_text_file(path: str, encoding: str = "utf-8") -> str:
    with open(path, "r", encoding=encoding) as f:
        return f.read()


def _write_text_file(path: str, text: str, encoding: str = "utf-8") -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding=encoding) as f:
        f.write(text)


def compare_transcript(expected_text: str, got_text: str, *, strip_colors: bool = True) -> TranscriptResult:
    exp = normalize_line_endings(expected_text)
    got = normalize_line_endings(got_text)

    if strip_colors:
        exp = strip_ansi(exp)
        got = strip_ansi(got)

    exp_lines = exp.splitlines()
    got_lines = got.splitlines()

    if exp_lines == got_lines:
        return TranscriptResult(True, exp_lines, got_lines, "")

    # Find first mismatch for a useful message
    max_len = max(len(exp_lines), len(got_lines))
    idx = 0
    for i in range(max_len):
        e = exp_lines[i] if i < len(exp_lines) else None
        g = got_lines[i] if i < len(got_lines) else None
        if e != g:
            idx = i
            break

    message = f"Transcript mismatch at line {idx+1}: expected={exp_lines[idx] if idx < len(exp_lines) else '<EOF>'!r}, got={got_lines[idx] if idx < len(got_lines) else '<EOF>'!r}"
    return TranscriptResult(False, exp_lines, got_lines, message)


def parse_transcript(transcript_text: str, *, prompt: str = "(Cmd) ") -> List[str]:
    """
    Parse a transcript into a list of input command lines.

    Expected transcript format is compatible with a common cmd2 transcript style:
      (Cmd) command args
      output...
      (Cmd) another_command

    Only lines beginning with the prompt are treated as command lines; the prompt
    itself is stripped.
    """
    transcript_text = normalize_line_endings(transcript_text)
    cmds: List[str] = []
    for line in transcript_text.splitlines():
        if line.startswith(prompt):
            cmds.append(line[len(prompt) :])
    return cmds


def run_transcript(
    app,
    transcript_text: str,
    *,
    prompt: Optional[str] = None,
    strip_colors: bool = True,
    raise_on_failure: bool = True,
):
    """
    Run commands from transcript_text through app and compare against transcript_text.

    This uses the same prompt string used by app (or an override).
    """
    use_prompt = prompt if prompt is not None else getattr(app, "prompt", "(Cmd) ")
    commands = parse_transcript(transcript_text, prompt=use_prompt)

    out_buf = io.StringIO()
    # Simulate transcript: echo prompts + commands, then capture output lines in between.
    for cmd in commands:
        out_buf.write(f"{use_prompt}{cmd}\n")
        # Run and capture output of the command.
        with capture_output(merge_stderr=True) as buf:
            app.onecmd_plus_hooks(cmd)
        out = buf.getvalue()
        if out:
            out_buf.write(out)
            if not out.endswith("\n"):
                out_buf.write("\n")

    got_text = out_buf.getvalue().rstrip("\n") + "\n"
    exp_text = transcript_text.rstrip("\n") + "\n"

    res = compare_transcript(exp_text, got_text, strip_colors=strip_colors)
    if (not res.matched) and raise_on_failure:
        raise AssertionError(res.message)
    return res


__all__ = [
    "strip_ansi",
    "normalize_line_endings",
    "capture_output",
    "compare_transcript",
    "parse_transcript",
    "run_transcript",
    "TranscriptResult",
]