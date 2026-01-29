from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Union

from .utils import strip_ansi, ensure_str, capture_output


@dataclass
class TranscriptFailure:
    command: str
    expected: str
    actual: str
    diff: str


@dataclass
class TranscriptResult:
    path: Path
    passed: bool
    failures: List[TranscriptFailure]


class TranscriptRunner:
    def __init__(self, app, *, strip_ansi_codes: bool = True, prompt: Optional[str] = None, merge_streams: bool = True):
        self.app = app
        self.strip_ansi_codes = strip_ansi_codes
        self.prompt = prompt if prompt is not None else getattr(app, "prompt", "> ")
        self.merge_streams = merge_streams

    def _norm(self, s: str) -> str:
        s = ensure_str(s).replace("\r\n", "\n").replace("\r", "\n")
        if self.strip_ansi_codes:
            s = strip_ansi(s)
        return s

    def _parse_transcript(self, text: str):
        """
        Minimal transcript format:
          <prompt><command>
          <expected output line 1>
          ...
          <prompt><next command>
          ...

        Returns list of (command, expected_output_block_string).
        """
        prompt = self.prompt
        lines = text.splitlines()
        items = []
        cur_cmd = None
        cur_out = []
        for line in lines:
            if line.startswith(prompt):
                if cur_cmd is not None:
                    items.append((cur_cmd, "\n".join(cur_out).rstrip("\n")))
                cur_cmd = line[len(prompt) :].lstrip()
                cur_out = []
            else:
                # expected output
                cur_out.append(line)
        if cur_cmd is not None:
            items.append((cur_cmd, "\n".join(cur_out).rstrip("\n")))
        return items

    def run(self, transcript_path: Union[str, Path]) -> TranscriptResult:
        path = Path(transcript_path)
        text = path.read_text(encoding="utf-8")
        text = self._norm(text)
        script = self._parse_transcript(text)

        failures: List[TranscriptFailure] = []
        for command, expected in script:
            with capture_output() as (out, err):
                # route app output to sys.std* redirection via capture_output; but app may use self.stdout/self.stderr
                # So temporarily point app streams at these buffers.
                old_out, old_err = getattr(self.app, "stdout", None), getattr(self.app, "stderr", None)
                try:
                    self.app.stdout = out
                    self.app.stderr = err
                    self.app.onecmd(command)
                finally:
                    self.app.stdout = old_out
                    self.app.stderr = old_err

            actual_out = out.getvalue()
            actual_err = err.getvalue()
            actual = actual_out + (actual_err if self.merge_streams else "")
            actual = self._norm(actual).rstrip("\n")

            exp = expected.rstrip("\n")
            if actual != exp:
                diff = self._simple_diff(exp, actual)
                failures.append(TranscriptFailure(command=command, expected=exp, actual=actual, diff=diff))

        return TranscriptResult(path=path, passed=(len(failures) == 0), failures=failures)

    @staticmethod
    def _simple_diff(expected: str, actual: str) -> str:
        exp_lines = expected.splitlines()
        act_lines = actual.splitlines()
        out = []
        maxn = max(len(exp_lines), len(act_lines))
        for i in range(maxn):
            e = exp_lines[i] if i < len(exp_lines) else ""
            a = act_lines[i] if i < len(act_lines) else ""
            if e == a:
                out.append("  " + e)
            else:
                out.append("- " + e)
                out.append("+ " + a)
        return "\n".join(out)


def run_transcript_tests(app, transcript_files: Sequence[Union[str, Path]], *, fail_on_exception: bool = True, strip_ansi_codes: bool = True):
    # fail_on_exception kept for signature compatibility; this minimal runner doesn't suppress exceptions from app.onecmd.
    runner = TranscriptRunner(app, strip_ansi_codes=strip_ansi_codes)
    results = []
    for p in transcript_files:
        results.append(runner.run(p))
    return results