from __future__ import annotations

import argparse
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import yaml
from openai import OpenAI

# 复用原评测逻辑（不改 measure_generated.py）
try:
    from .measure_generated import run_all_tests  # type: ignore
except Exception:
    from measure_generated import run_all_tests  # type: ignore


ROOT = Path(__file__).resolve().parents[1]

FILE_BLOCK_RE = re.compile(
    r"<file:name=(?P<name>[^>]+)>\s*(?P<content>.*?)\s*</file>",
    re.DOTALL | re.MULTILINE,
)

PLAN_BLOCK_RE = re.compile(
    r"<plan>\s*(?P<content>.*?)\s*</plan>",
    re.DOTALL | re.MULTILINE,
)


# ----------------------------
# IO
# ----------------------------
def load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def parse_file_blocks(raw: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for m in FILE_BLOCK_RE.finditer(raw or ""):
        name = (m.group("name") or "").strip()
        content = m.group("content") or ""
        if name:
            out.append((name, content))
    return out


def parse_plan(raw: str) -> str:
    raw = raw or ""
    m = PLAN_BLOCK_RE.search(raw)
    if not m:
        return raw.strip()
    return (m.group("content") or "").strip()


# ----------------------------
# OpenAI call
# ----------------------------
def call_model(prompt: str, model: str) -> str:
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("openai_base_url")
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("openai_api_key")

    client_kwargs: Dict[str, Any] = {}
    if base_url:
        client_kwargs["base_url"] = base_url
    if api_key:
        client_kwargs["api_key"] = api_key

    client = OpenAI(**client_kwargs)

    print("Using API configuration:")
    print(f"  Base URL: {base_url or '(default)'}")
    print(f"  Model: {model}")

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a careful software engineer who follows instructions exactly."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return (resp.choices[0].message.content or "").strip()


# ----------------------------
# Agent self-tests runner (generated tests)
# ----------------------------
def run_agent_tests(repo_root: Path, tests_dir: Path, timeout_s: int = 180) -> Dict[str, Any]:
    """
    只用于 agent 的自测（生成的测试用例），不参与 benchmark 计分。
    """
    env = os.environ.copy()
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(repo_root) + (os.pathsep + existing_pp if existing_pp else "")

    cmd = [sys.executable, "-m", "pytest", str(tests_dir), "-q"]
    print(f"[M1] Running agent tests: {' '.join(cmd)}")

    try:
        p = subprocess.run(
            cmd,
            cwd=str(ROOT),  # 与 official runner 一致：从仓库根运行
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout_s,
        )
        return {"returncode": p.returncode, "stdout": p.stdout or "", "timeout": False}
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") if isinstance(e.stdout, str) else ""
        return {"returncode": 124, "stdout": out + "\n[M1] TIMEOUT\n", "timeout": True}
    except Exception as e:
        return {"returncode": 1, "stdout": f"[M1] ERROR running pytest: {e}\n", "timeout": False}


# ----------------------------
# Prompts (M1)
# ----------------------------
def build_plan_prompt(task: Dict[str, Any]) -> str:
    desc = (task.get("description") or "").strip()
    api_contract = (task.get("api_contract") or "").strip()
    api_block = f"\n\n[API CONTRACT]\n{api_contract}\n" if api_contract else ""

    files = task.get("files", []) or []
    file_list = "\n".join([f"- {x.get('path')}" for x in files if isinstance(x, dict) and x.get("path")])

    return f"""You are planning the implementation for a Python repository.

[Task]
{desc}{api_block}

[Required files]
{file_list}

[Output format]
Return ONLY raw text, no markdown, inside exactly one block:

<plan>
1) Repository layout and import graph
2) Public APIs to implement (modules/classes/functions)
3) Key behaviors & edge cases
4) Minimal internal test plan (what to test and why)
5) Risks (dependencies, tricky behaviors) and mitigations
</plan>
"""


def build_generate_prompt(task: Dict[str, Any], plan: str) -> str:
    desc = (task.get("description") or "").strip()
    api_contract = (task.get("api_contract") or "").strip()
    api_block = f"\n\n[API CONTRACT]\n{api_contract}\n" if api_contract else ""

    files = task.get("files", []) or []
    file_list = "\n".join([f"- {x.get('path')}" for x in files if isinstance(x, dict) and x.get("path")])

    plan = (plan or "").strip()
    plan_block = f"\n\n[PLAN]\n{plan}\n" if plan else ""

    return f"""You are generating a Python repository AND a small internal test suite for one-round self-verification.

[Task]
{desc}{api_block}{plan_block}

[Required files]
{file_list}

[Agent self-tests requirement]
- You MUST also create internal tests under directory: _agent_tests/
- Use pytest only; no additional third-party libraries.
- Tests should be meaningful (cover key behaviors & edge cases), and should FAIL if requirements are not met.
- These tests are for internal checking only, separate from the official benchmark tests.

[Output format]
Return ONLY raw text, no markdown. Use one or more blocks like:

<file:name=path/to/file.py>
# file content here
</file>

Include at least one test file, e.g.:
<file:name=_agent_tests/test_agent_basic.py>
...
</file>

Each <file:...> block MUST contain the complete content of that file.
"""


def build_fix_prompt(task: Dict[str, Any], plan: str, agent_test_output: str) -> str:
    desc = (task.get("description") or "").strip()
    api_contract = (task.get("api_contract") or "").strip()
    api_block = f"\n\n[API CONTRACT]\n{api_contract}\n" if api_contract else ""
    plan = (plan or "").strip()
    plan_block = f"\n\n[PLAN]\n{plan}\n" if plan else ""

    # 控制反馈长度，避免 prompt 过大
    agent_test_output = (agent_test_output or "")
    if len(agent_test_output) > 12000:
        agent_test_output = agent_test_output[-12000:]

    return f"""You are performing ONE repair iteration based on internal agent tests.

[Task]
{desc}{api_block}{plan_block}

[Agent test failure output]
{agent_test_output}

[Rules]
- You have only ONE repair attempt.
- Fix the repository implementation so that agent tests pass.
- DO NOT weaken or delete tests. Prefer fixing code.
- Do not introduce new third-party dependencies.

[Output format]
Return ONLY raw text, no markdown. Output ONLY the files you changed, using blocks:

<file:name=relative/path.py>
... full file content ...
</file>
"""


# ----------------------------
# Main M1 pipeline
# ----------------------------
def write_files_from_blocks(repo_root: Path, blocks: List[Tuple[str, str]], skip_paths: Optional[set] = None) -> None:
    skip_paths = skip_paths or set()
    for rel_path, content in blocks:
        rel_path = rel_path.lstrip("/\\")
        if rel_path in skip_paths:
            continue
        dst = repo_root / rel_path
        save_text(dst, content)
        print(f"Saved file: {dst}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, type=str, help="Path to task yaml")
    parser.add_argument("--model", default=os.environ.get("RACB_MODEL", "gpt-4o-mini"), type=str)

    parser.add_argument("--skip-generation", action="store_true", help="Skip generation and evaluate existing repo")

    # 输出隔离（默认不覆盖 baseline）
    parser.add_argument("--generated-root", default="generation_m1", type=str)
    parser.add_argument("--results-root", default="results_m1", type=str)

    # Agent tests runtime knobs
    parser.add_argument("--agent-timeout-s", default=180, type=int, help="Timeout for running agent tests")
    parser.add_argument("--always-fix-once", action="store_true", help="Run the fix step once even if agent tests pass")

    args = parser.parse_args()

    task_file = Path(args.task).resolve()
    task = load_yaml(task_file)
    project_name = task_file.parent.name

    generated_repo = (ROOT / args.generated_root / project_name).resolve()
    _ensure_dir(generated_repo)

    plan_text = ""
    agent_tests_dir = generated_repo / "_agent_tests"
    agent_before = {"returncode": 1, "stdout": "", "timeout": False}
    agent_after = {"returncode": 1, "stdout": "", "timeout": False}

    if not args.skip_generation:
        # Stage-0: Analysis/Plan
        print("[M1] Stage-0: analysis / planning...")
        raw_plan = call_model(build_plan_prompt(task), model=args.model)
        plan_text = parse_plan(raw_plan)
        save_text(generated_repo / "_m1_plan_raw.txt", raw_plan)
        save_text(generated_repo / "_m1_plan.txt", plan_text)

        # Stage-1: Generate code + internal tests
        print("[M1] Stage-1: generating code + agent tests...")
        raw_gen = call_model(build_generate_prompt(task, plan_text), model=args.model)
        save_text(generated_repo / "_m1_raw_model_output.txt", raw_gen)

        blocks = parse_file_blocks(raw_gen)
        if not blocks:
            raise ValueError(f"Model output did not contain any <file:name=...> blocks. Saved: {generated_repo / '_m1_raw_model_output.txt'}")

        write_files_from_blocks(generated_repo, blocks)

        # Stage-2: Run agent tests (before fix)
        print("[M1] Stage-2: running agent tests (before fix)...")
        if not agent_tests_dir.exists():
            save_text(generated_repo / "_m1_agent_before.log", "[M1] No _agent_tests directory generated.\n")
            agent_before = {"returncode": 1, "stdout": "[M1] No _agent_tests directory generated.\n", "timeout": False}
        else:
            agent_before = run_agent_tests(generated_repo, agent_tests_dir, timeout_s=args.agent_timeout_s)
            save_text(generated_repo / "_m1_agent_before.log", agent_before.get("stdout", ""))

        # Stage-3: One repair (conditional)
        need_fix = args.always_fix_once or (int(agent_before.get("returncode", 1)) != 0)
        if need_fix:
            print("[M1] Stage-3: one-shot repair...")
            raw_fix = call_model(build_fix_prompt(task, plan_text, agent_before.get("stdout", "")), model=args.model)
            save_text(generated_repo / "_m1_fix_raw_model_output.txt", raw_fix)

            fix_blocks = parse_file_blocks(raw_fix)
            if not fix_blocks:
                save_text(generated_repo / "_m1_fix_apply_status.txt", "No file blocks in fix output; nothing applied.\n")
            else:
                # 修复阶段原则上不允许改 agent tests；只修代码
                write_files_from_blocks(generated_repo, fix_blocks, skip_paths={"_agent_tests/test_agent_basic.py"} if False else set())

            # Stage-3b: Run agent tests (after fix)
            print("[M1] Stage-3b: running agent tests (after fix)...")
            if agent_tests_dir.exists():
                agent_after = run_agent_tests(generated_repo, agent_tests_dir, timeout_s=args.agent_timeout_s)
                save_text(generated_repo / "_m1_agent_after.log", agent_after.get("stdout", ""))
            else:
                agent_after = {"returncode": 1, "stdout": "[M1] No _agent_tests directory.\n", "timeout": False}
                save_text(generated_repo / "_m1_agent_after.log", agent_after["stdout"])

        else:
            save_text(generated_repo / "_m1_fix_apply_status.txt", "Agent tests passed; fix step skipped.\n")

        # Record status summary
        save_text(
            generated_repo / "_m1_status.txt",
            f"agent_before_returncode={agent_before.get('returncode')}\n"
            f"agent_after_returncode={agent_after.get('returncode')}\n"
        )

    else:
        print(f"跳过代码生成与 agent 测试，直接评估已存在的代码仓库: {generated_repo}")

    # Stage-4: Official benchmark evaluation (NOT using agent tests)
    print("[M1] Stage-4: running official benchmark evaluation...")
    results_root = (ROOT / args.results_root).resolve()
    results_root.mkdir(parents=True, exist_ok=True)
    result_file = results_root / f"{project_name}_results.yaml"

    run_all_tests(task_file, generated_repo, result_file)
    print(f"Wrote results to: {result_file}")


if __name__ == "__main__":
    main()
