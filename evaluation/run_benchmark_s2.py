from __future__ import annotations

import argparse
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

REQ_BLOCK_RE = re.compile(
    r"<requirements>\s*(?P<content>.*?)\s*</requirements>",
    re.DOTALL | re.MULTILINE,
)


# ----------------------------
# basic IO
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


def parse_requirements(raw: str) -> str:
    """
    解析 <requirements>...</requirements>。如果没有标签，降级用全文。
    返回适合写入 requirements.txt 的文本（去掉空行、保留注释）。
    """
    raw = raw or ""
    m = REQ_BLOCK_RE.search(raw)
    body = (m.group("content") if m else raw) or ""
    lines = []
    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue
        # 允许注释
        lines.append(s)
    return "\n".join(lines).strip()


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
            {"role": "system", "content": "You are a helpful code generator."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return (resp.choices[0].message.content or "").strip()


# ----------------------------
# prompts (M3)
# ----------------------------
def build_dependency_prompt(task: Dict[str, Any]) -> str:
    desc = (task.get("description") or "").strip()
    files = task.get("files", []) or []
    file_list = "\n".join([f"- {x.get('path')}" for x in files if isinstance(x, dict) and x.get("path")])

    api_contract = (task.get("api_contract") or "").strip()
    api_contract_block = f"\n\n[API CONTRACT]\n{api_contract}\n" if api_contract else ""

    return f"""You are preparing Python third-party dependencies for a repository.

[Task]
{desc}{api_contract_block}

[Required files]
{file_list}

[Goal]
Output a minimal, correct list of third-party pip dependencies required to run the tests.
- Only include non-stdlib packages.
- Do NOT include "pytest" unless the project requires it at runtime (tests already have pytest).
- Prefer minimal versions; avoid over-pinning unless necessary.
- If unsure, choose the most standard package name for the import.

[Output format]
Return ONLY raw text, no markdown, inside exactly one block:

<requirements>
package1
package2>=x.y
package3==a.b.c
</requirements>
"""


def build_code_prompt_with_dep_hint(task: Dict[str, Any], requirements_txt: str) -> str:
    desc = (task.get("description") or "").strip()
    files = task.get("files", []) or []
    file_list = "\n".join([f"- {x.get('path')}" for x in files if isinstance(x, dict) and x.get("path")])

    api_contract = (task.get("api_contract") or "").strip()
    api_contract_block = f"\n\n[API CONTRACT]\n{api_contract}\n" if api_contract else ""

    req_block = (requirements_txt or "").strip()
    req_hint = f"\n\n[DEPENDENCIES]\nThe following requirements.txt will be installed before tests:\n{req_block}\n" if req_block else ""

    return f"""You are generating a Python repository.

[Task]
{desc}{api_contract_block}{req_hint}

[Required files]
{file_list}

[Dependency rule]
You MUST NOT import any third-party library outside the provided dependencies list.
If you need additional third-party packages, redesign to avoid them.

[Output format]
Return ONLY raw text, no markdown. Use one or more blocks like:

<file:name=path/to/file.py>
# file content here
</file>

Each <file:...> block MUST contain the complete content of that file.
"""


# ----------------------------
# dependency installation
# ----------------------------
def pip_install_requirements(repo_root: Path, timeout_s: int = 900) -> bool:
    req = repo_root / "requirements.txt"
    if not req.exists():
        print("[M3] No requirements.txt found, skip pip install.")
        return True

    log_path = repo_root / "_m3_pip_install.log"
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(req)]
    env = os.environ.copy()
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PIP_NO_INPUT"] = "1"

    print(f"[M3] Installing dependencies: {cmd}")
    try:
        p = subprocess.run(
            cmd,
            cwd=str(repo_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout_s,
        )
        save_text(log_path, p.stdout or "")
        ok = (p.returncode == 0)
        print(f"[M3] pip install returncode={p.returncode}, log={log_path}")
        return ok
    except subprocess.TimeoutExpired:
        save_text(log_path, "pip install TIMEOUT\n")
        print(f"[M3] pip install TIMEOUT, log={log_path}")
        return False
    except Exception as e:
        save_text(log_path, f"pip install ERROR: {e}\n")
        print(f"[M3] pip install ERROR: {e}, log={log_path}")
        return False


# ----------------------------
# generation (M3)
# ----------------------------
def generate_code_with_model_m3(task: Dict[str, Any], output_repo: Path, model: str, requirements_txt: str) -> None:
    prompt = build_code_prompt_with_dep_hint(task, requirements_txt)
    print("[M3] Calling model to generate repository code...")
    raw = call_model(prompt, model=model)

    save_text(output_repo / "_m3_raw_model_output.txt", raw)

    blocks = parse_file_blocks(raw)
    if not blocks:
        raise ValueError(f"Model output did not contain any <file:name=...> blocks. Saved: {output_repo / '_m3_raw_model_output.txt'}")

    # 防止模型覆盖我们自动生成的依赖文件（确保“生成依赖→安装→测试”链路稳定）
    skip_names = {"requirements.txt", "pyproject.toml", "setup.py", "setup.cfg"}

    for rel_path, content in blocks:
        rel_path = rel_path.lstrip("/\\")
        if rel_path in skip_names:
            print(f"[M3] Skip writing {rel_path} (managed by M3 pipeline).")
            continue
        dst = output_repo / rel_path
        save_text(dst, content)
        print(f"Saved file: {dst}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, type=str, help="Path to task yaml")
    parser.add_argument("--model", default=os.environ.get("RACB_MODEL", "gpt-4o-mini"), type=str)

    parser.add_argument("--skip-generation", action="store_true", help="Skip generation and evaluate existing repo")
    parser.add_argument("--skip-install", action="store_true", help="Skip pip install even if requirements.txt exists")

    # 输出隔离（默认不覆盖 baseline）
    parser.add_argument("--generated-root", default="generation_m3", type=str)
    parser.add_argument("--results-root", default="results_m3", type=str)

    args = parser.parse_args()

    task_file = Path(args.task).resolve()
    task = load_yaml(task_file)
    project_name = task_file.parent.name

    generated_repo = (ROOT / args.generated_root / project_name).resolve()
    _ensure_dir(generated_repo)

    if not args.skip_generation:
        # Stage-1: 生成依赖列表
        print("[M3] Stage-1: generating requirements.txt ...")
        dep_prompt = build_dependency_prompt(task)
        raw_req = call_model(dep_prompt, model=args.model)
        req_txt = parse_requirements(raw_req)

        save_text(generated_repo / "_m3_requirements_raw.txt", raw_req)
        save_text(generated_repo / "requirements.txt", req_txt + ("\n" if req_txt else ""))

        # Stage-2: 安装依赖
        if not args.skip_install:
            ok = pip_install_requirements(generated_repo)
            save_text(generated_repo / "_m3_install_status.txt", f"ok={ok}\n")
        else:
            print("[M3] Skip pip install by --skip-install")

        # Stage-3: 生成仓库代码（带依赖提示）
        print("[M3] Stage-3: generating code with dependency hint ...")
        generate_code_with_model_m3(task, generated_repo, args.model, req_txt)

    else:
        print(f"跳过代码生成，直接评估已存在的代码仓库: {generated_repo}")

    # Stage-4: 评测（复用原有逻辑）
    results_root = (ROOT / args.results_root).resolve()
    results_root.mkdir(parents=True, exist_ok=True)
    result_file = results_root / f"{project_name}_results.yaml"

    run_all_tests(task_file, generated_repo, result_file)
    print(f"Wrote results to: {result_file}")


if __name__ == "__main__":
    main()
