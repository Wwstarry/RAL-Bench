import argparse
import os
import re
import sys
import time
import yaml
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, List

import psutil
import statistics

ROOT = Path(__file__).resolve().parents[1]

REPO_ROOT_ENV = "RACB_REPO_ROOT"
PKG_NAME_ENV = "RACB_PACKAGE_NAME"

SEC_PREFIX = "SECURITY_METRICS"
MAINT_PREFIX = "MAINT_METRICS"


def load_task_config(task_file: Path) -> Dict[str, Any]:
    with open(task_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _resolve_test_path(project_name: str, test_path: str) -> Path:
    p = Path(test_path)
    if p.is_absolute():
        return p
    cand = (ROOT / p).resolve()
    if cand.exists():
        return cand
    return (ROOT / "tests" / project_name / Path(test_path).name).resolve()


def _parse_pytest_counts(output: str) -> Dict[str, int]:
    passed = failed = skipped = 0
    total = 0

    # 1) Prefer "collected N items"
    m = re.search(r"collected\s+(\d+)\s+items?", output)
    if m:
        total = int(m.group(1))

    # 2) Parse summary like "1 passed, 2 failed, 1 skipped"
    m = re.search(r"(\d+)\s+passed", output)
    if m:
        passed = int(m.group(1))
    m = re.search(r"(\d+)\s+failed", output)
    if m:
        failed = int(m.group(1))
    m = re.search(r"(\d+)\s+skipped", output)
    if m:
        skipped = int(m.group(1))

    # If total unknown, infer from passed/failed/skipped
    if total == 0:
        total = passed + failed + skipped

    # If still unknown, fallback to 1 when returncode != 0
    if total == 0:
        total = 1 if ("FAILED" in output or "ERROR" in output) else 0

    return {"passed": passed, "failed": failed, "skipped": skipped, "total": total}


def _parse_kv_metrics_line(output: str, prefix: str) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    pattern = re.compile(rf"^{re.escape(prefix)}\s+(.*)$", re.MULTILINE)
    matches = pattern.findall(output or "")
    if not matches:
        return metrics
    blob = matches[-1].strip()
    for part in blob.split():
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        try:
            metrics[k] = float(v)
        except Exception:
            continue
    return metrics


def _kill_process_tree(proc: psutil.Popen) -> None:
    try:
        children = proc.children(recursive=True)
    except Exception:
        children = []
    for c in children:
        try:
            c.kill()
        except Exception:
            pass
    try:
        proc.kill()
    except Exception:
        pass


def _run_pytest_with_sampling(
    test_path: Path,
    repo_root: Path,
    extra_env: Dict[str, str],
    timeout_s: float,
    add_s: bool,
    sample_interval_s: float = 0.10,
) -> Dict[str, Any]:
    env = os.environ.copy()
    env.update(extra_env)

    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(repo_root) + (os.pathsep + existing_pp if existing_pp else "")

    cmd = [sys.executable, "-m", "pytest", str(test_path)]
    if add_s:
        cmd.append("-s")
    cmd.append("-q")

    proc = psutil.Popen(
        cmd,
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    try:
        proc.cpu_percent(interval=None)
    except Exception:
        pass

    mem_samples: List[int] = []
    cpu_samples: List[float] = []
    stdout_chunks: List[str] = []

    start = time.perf_counter()
    deadline = start + timeout_s

    while True:
        now = time.perf_counter()
        if now > deadline:
            _kill_process_tree(proc)
            out = "".join(stdout_chunks)
            return {
                "returncode": 124,
                "stdout": out,
                "elapsed_time_s": round(now - start, 6),
                "avg_memory_mb": 0.0,
                "avg_cpu_percent": 0.0,
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "total": 1,
                "timeout": True,
            }

        if proc.poll() is not None:
            break

        if proc.stdout is not None:
            try:
                line = proc.stdout.readline()
            except Exception:
                line = ""
            if line:
                stdout_chunks.append(line)
                print(line, end="")

        # sample rss/cpu of proc + children
        rss_total = 0
        cpu_total = 0.0
        try:
            children = proc.children(recursive=True)
        except Exception:
            children = []
        for p in [proc] + children:
            try:
                rss_total += p.memory_info().rss
            except Exception:
                pass
            try:
                cpu_total += p.cpu_percent(interval=None)
            except Exception:
                pass

        mem_samples.append(rss_total)
        cpu_samples.append(cpu_total)
        time.sleep(sample_interval_s)

    elapsed = time.perf_counter() - start

    tail = ""
    if proc.stdout is not None:
        try:
            tail = proc.stdout.read() or ""
        except Exception:
            tail = ""
    if tail:
        stdout_chunks.append(tail)
        print(tail, end="")

    out = "".join(stdout_chunks)
    counts = _parse_pytest_counts(out)

    avg_mem_mb = (statistics.mean(mem_samples) / (1024 * 1024)) if mem_samples else 0.0
    avg_cpu = statistics.mean(cpu_samples) if cpu_samples else 0.0

    result: Dict[str, Any] = {
        "returncode": int(proc.returncode) if proc.returncode is not None else 1,
        "stdout": out,
        "elapsed_time_s": round(elapsed, 6),
        "avg_memory_mb": round(avg_mem_mb, 2),
        "avg_cpu_percent": round(avg_cpu, 2),
        **counts,
    }

    if add_s:
        # Attach metrics (if any)
        sec = _parse_kv_metrics_line(out, SEC_PREFIX)
        if sec:
            result.setdefault("metrics", {}).update(sec)
        maint = _parse_kv_metrics_line(out, MAINT_PREFIX)
        if maint:
            result.setdefault("metrics", {}).update(maint)

    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("task_file", type=Path)
    ap.add_argument("--target-env", required=True)
    ap.add_argument("--reference-value", default="reference")
    args = ap.parse_args()

    task_file: Path = args.task_file
    task = load_task_config(task_file)

    project_name = task_file.parent.name
    ref_repo = (ROOT / (task.get("reference_repository") or "")).resolve()
    if not ref_repo.exists():
        raise FileNotFoundError(f"Reference repository not found: {ref_repo}")

    package_name = (task.get("package") or {}).get("name") or ""

    test_suite = task.get("test_suite") or {}
    timeouts = task.get("suite_timeouts_s") or {}
    default_timeout = float(timeouts.get("default", 60))

    baseline: Dict[str, Any] = task.get("baseline_metrics") or {}
    task["baseline_metrics"] = baseline

    for test_type, test_rel in test_suite.items():
        test_path = _resolve_test_path(project_name, str(test_rel))
        timeout_s = float(timeouts.get(test_type, default_timeout))
        add_s = test_type in {"security", "maintainability"}

        extra_env = {
            args.target_env: args.reference_value,
            REPO_ROOT_ENV: str(ref_repo),
        }
        if package_name:
            extra_env[PKG_NAME_ENV] = package_name

        print("=" * 132)
        print(f"Running reference {project_name}:{test_type} -> {test_path} (timeout={timeout_s}s)")

        r = _run_pytest_with_sampling(
            test_path=test_path,
            repo_root=ref_repo,
            extra_env=extra_env,
            timeout_s=timeout_s,
            add_s=add_s,
        )

        entry: Dict[str, Any] = baseline.get(test_type) or {}
        entry[f"{test_type}_suite_time_s"] = float(r.get("elapsed_time_s", 0.0) or 0.0)
        entry[f"{test_type}_tests_total"] = int(r.get("total", 0) or 0)

        if test_type == "resource":
            entry["avg_memory_mb"] = float(r.get("avg_memory_mb", 0.0) or 0.0)
            entry["avg_cpu_percent"] = float(r.get("avg_cpu_percent", 0.0) or 0.0)

        if test_type in {"security", "maintainability"}:
            metrics = r.get("metrics") or {}
            if metrics:
                entry["metrics"] = metrics

        baseline[test_type] = entry

    print("Measured baseline_metrics:")
    print(task["baseline_metrics"])

    with open(task_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(task, f, allow_unicode=True, sort_keys=False)

    print(f"Updated baseline_metrics in {task_file}")


if __name__ == "__main__":
    main()
