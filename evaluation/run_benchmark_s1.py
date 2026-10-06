"""S1: one feedback-driven self-repair step using model-generated tests."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml
from openai import OpenAI

from .measure_generated import run_all_tests

ROOT = Path(__file__).resolve().parents[1]
FILE_BLOCK_RE = re.compile(r"<file:name=(?P<name>[^>]+)>\s*(?P<content>.*?)\s*</file>", re.DOTALL)


def load_task(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def call_model(prompt: str, model: str) -> str:
    kwargs: Dict[str, Any] = {}
    if os.environ.get("OPENAI_BASE_URL"):
        kwargs["base_url"] = os.environ["OPENAI_BASE_URL"]
    if os.environ.get("OPENAI_API_KEY"):
        kwargs["api_key"] = os.environ["OPENAI_API_KEY"]
    response = OpenAI(**kwargs).chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful code generator."},
            {"role": "user", "content": prompt},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def file_blocks(raw: str) -> List[Tuple[str, str]]:
    return [(m.group("name").strip(), m.group("content")) for m in FILE_BLOCK_RE.finditer(raw)]


def write_blocks(root: Path, blocks: List[Tuple[str, str]], *, allow_tests: bool) -> None:
    root = root.resolve()
    for name, content in blocks:
        rel = Path(name.lstrip("/\\"))
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"Unsafe model output path: {name}")
        if not allow_tests and rel.parts and rel.parts[0] == "_agent_tests":
            continue
        destination = (root / rel).resolve()
        if root not in destination.parents:
            raise ValueError(f"Unsafe model output path: {name}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


def task_context(task: Dict[str, Any]) -> str:
    files = "\n".join(
        f"- {item['path']}" for item in task.get("files", []) if isinstance(item, dict) and item.get("path")
    )
    return f"[Task]\n{task.get('description', '').strip()}\n\n[Public surface]\n{task.get('api_contract', '').strip()}\n\n[Required files]\n{files}"


def generation_prompt(task: Dict[str, Any]) -> str:
    return f"""Generate a complete Python repository and a small meaningful pytest suite under _agent_tests/.

{task_context(task)}

Return only complete files as <file:name=relative/path>...</file> blocks. Include at least one _agent_tests/test_*.py file. Do not use the hidden benchmark tests.
"""


def repair_prompt(task: Dict[str, Any], feedback: str) -> str:
    return f"""Perform exactly one repair iteration on the generated repository.

{task_context(task)}

[Generated-test feedback]
{feedback[-12000:]}

Return only changed implementation files as <file:name=relative/path>...</file> blocks. Do not modify or delete _agent_tests.
"""


def run_agent_tests(repo: Path, timeout: int) -> str:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "_agent_tests", "-q"],
            cwd=repo,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return result.stdout or f"pytest exited with {result.returncode}"
    except subprocess.TimeoutExpired as exc:
        return (exc.stdout or "") + "\nGenerated tests timed out."


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--model", default=os.environ.get("RACB_MODEL", "gpt-4o-mini"))
    parser.add_argument("--skip-generation", action="store_true")
    parser.add_argument("--generated-root", default="generation_s1")
    parser.add_argument("--results-root", default="results_s1")
    parser.add_argument("--agent-timeout-s", default=180, type=int)
    args = parser.parse_args()

    task_file = args.task.resolve()
    task = load_task(task_file)
    project = task_file.parent.name
    generated_repo = (ROOT / args.generated_root / project).resolve()
    generated_repo.mkdir(parents=True, exist_ok=True)

    if not args.skip_generation:
        blocks = file_blocks(call_model(generation_prompt(task), args.model))
        if not blocks:
            raise ValueError("Initial response contained no file blocks")
        write_blocks(generated_repo, blocks, allow_tests=True)
        feedback = run_agent_tests(generated_repo, args.agent_timeout_s)
        repaired = file_blocks(call_model(repair_prompt(task, feedback), args.model))
        if not repaired:
            raise ValueError("Repair response contained no file blocks")
        write_blocks(generated_repo, repaired, allow_tests=False)

    result_file = (ROOT / args.results_root / f"{project}_results.yaml").resolve()
    run_all_tests(task_file, generated_repo, result_file)


if __name__ == "__main__":
    main()
