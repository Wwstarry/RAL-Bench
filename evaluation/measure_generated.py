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

TEST_TYPES: List[str] = [
    "functional",
    "performance",
    "resource",
    "robustness",
    "security",
    "maintainability",
]

NON_FUNCTIONAL_WEIGHTS: Dict[str, float] = {
    "maintainability": 0.36,
    "security": 0.24,
    "robustness": 0.16,
    "performance": 0.12,
    "resource": 0.12,
}

_NON_TYPES: List[str] = ["maintainability", "security", "robustness", "performance", "resource"]

REPO_ROOT_ENV = "RACB_REPO_ROOT"
PKG_NAME_ENV = "RACB_PACKAGE_NAME"


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

    m = re.search(r"collected\s+(\d+)\s+items?", output)
    if m:
        total = int(m.group(1))

    m = re.search(r"(\d+)\s+passed", output)
    if m:
        passed = int(m.group(1))
    m = re.search(r"(\d+)\s+failed", output)
    if m:
        failed = int(m.group(1))
    m = re.search(r"(\d+)\s+skipped", output)
    if m:
        skipped = int(m.group(1))

    if total == 0:
        total = passed + failed + skipped

    if total == 0:
        total = 1 if ("FAILED" in output or "ERROR" in output) else 0

    return {"passed": passed, "failed": failed, "skipped": skipped, "total": total}


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


def _read_text_file_safely(p: Optional[Path]) -> str:
    if p is None:
        return ""
    try:
        if p.exists():
            return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        pass
    return ""


def _parse_kv_metrics_line(output: str, prefix: str) -> Dict[str, float]:
    if not output:
        return {}

    patterns = [
        re.compile(rf"^\s*{re.escape(prefix)}\s+(.*)$", re.MULTILINE),
        re.compile(rf"{re.escape(prefix)}\s+(.*)$", re.MULTILINE),
    ]

    matches: List[str] = []
    for pat in patterns:
        matches = pat.findall(output)
        if matches:
            break
    if not matches:
        return {}

    blob = matches[-1].strip()
    metrics: Dict[str, float] = {}
    for part in blob.split():
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        try:
            metrics[k] = float(v)
        except Exception:
            continue
    return metrics


def _extract_and_attach_metrics_force(result: Dict[str, Any], log_file: Optional[Path]) -> None:
    stdout_text = (result.get("stdout") or "")
    log_text = _read_text_file_safely(log_file)

    sec = _parse_kv_metrics_line(stdout_text, "SECURITY_METRICS")
    if not sec:
        sec = _parse_kv_metrics_line(log_text, "SECURITY_METRICS")
    if sec:
        result.setdefault("metrics", {}).update(sec)

    maint = _parse_kv_metrics_line(stdout_text, "MAINT_METRICS")
    if not maint:
        maint = _parse_kv_metrics_line(log_text, "MAINT_METRICS")
    if maint:
        result.setdefault("metrics", {}).update(maint)


def _run_pytest_with_sampling_and_stream(
    test_path: Path,
    repo_root: Path,
    extra_env: Dict[str, str],
    timeout_s: float,
    sample_interval_s: float = 0.10,
    log_file: Optional[Path] = None,
    add_s: bool = False,
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

    lf = None
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        lf = open(log_file, "w", encoding="utf-8")

    try:
        while True:
            now = time.perf_counter()
            if now > deadline:
                _kill_process_tree(proc)
                elapsed = now - start
                out = "".join(stdout_chunks)
                return {
                    "returncode": 124,
                    "stdout": out,
                    "elapsed_time_s": round(elapsed, 6),
                    "avg_memory_mb": round((statistics.mean(mem_samples) / (1024 * 1024)) if mem_samples else 0.0, 2),
                    "avg_cpu_percent": round(statistics.mean(cpu_samples) if cpu_samples else 0.0, 2),
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
                    if lf:
                        lf.write(line)
                        lf.flush()

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
            if lf:
                lf.write(tail)
                lf.flush()

        out = "".join(stdout_chunks)
        counts = _parse_pytest_counts(out)

        avg_mem_mb = (statistics.mean(mem_samples) / (1024 * 1024)) if mem_samples else 0.0
        avg_cpu = statistics.mean(cpu_samples) if cpu_samples else 0.0

        # 注意：proc.returncode 为 0 是合法值，不能用 `or 1`
        rc = proc.returncode
        returncode = int(rc) if rc is not None else 1

        return {
            "returncode": returncode,
            "stdout": out,
            "elapsed_time_s": round(elapsed, 6),
            "avg_memory_mb": round(avg_mem_mb, 2),
            "avg_cpu_percent": round(avg_cpu, 2),
            **counts,
        }
    finally:
        if lf:
            lf.close()


def run_test_suite(
    test_path: Path,
    repo_root: Path,
    target_env_var: Optional[str],
    target_value: str,
    timeout_s: float,
    log_file: Optional[Path],
    package_name: Optional[str],
    add_s: bool,
) -> Dict[str, Any]:
    extra_env: Dict[str, str] = {}
    if target_env_var:
        extra_env[target_env_var] = target_value
    extra_env[REPO_ROOT_ENV] = str(repo_root)
    if package_name:
        extra_env[PKG_NAME_ENV] = package_name

    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)

    result = _run_pytest_with_sampling_and_stream(
        test_path=test_path,
        repo_root=repo_root,
        extra_env=extra_env,
        timeout_s=timeout_s,
        log_file=log_file,
        add_s=add_s,
    )

    _extract_and_attach_metrics_force(result, log_file)

    if result.get("returncode", 1) != 0 and int(result.get("total", 0)) == 0:
        result["failed"] = 1
        result["total"] = 1

    return result


def _as_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _get_baseline_metric(baseline_for_type: Dict[str, Any], key: str) -> Optional[float]:
    if not isinstance(baseline_for_type, dict):
        return None
    if key in baseline_for_type:
        return _as_float(baseline_for_type.get(key))
    m = baseline_for_type.get("metrics")
    if isinstance(m, dict) and key in m:
        return _as_float(m.get(key))
    return None


def _smooth_compress_ratio(r: float) -> float:
    if r <= 0.0:
        return 0.0
    s = r / (1.0 + r)
    if s < 0.0:
        return 0.0
    if s > 1.0:
        return 1.0
    return s


def _as_int_preserve_zero(x: Any, default: int) -> int:
    # 只在 None / 转换失败时用 default；0 必须保留
    if x is None:
        return default
    try:
        return int(x)
    except Exception:
        return default


def calculate_score(test_type: str, test_result: Dict[str, Any], baseline_metrics: Dict[str, Any]) -> float:
    baseline_for_type = baseline_metrics.get(test_type, {}) if isinstance(baseline_metrics, dict) else {}

    passed = _as_int_preserve_zero(test_result.get("passed"), 0)
    failed = _as_int_preserve_zero(test_result.get("failed"), 0)
    total = _as_int_preserve_zero(test_result.get("total"), 0)

    # 关键修复：returncode==0 不能被当成 falsy 改成 1
    returncode = _as_int_preserve_zero(test_result.get("returncode"), 1)

    failed_suite = (failed > 0) or (returncode != 0)

    # 强可观测：把关键打分输入写到 suite 顶层，方便 grep
    test_result["score_inputs_passed"] = passed
    test_result["score_inputs_failed"] = failed
    test_result["score_inputs_total"] = total
    test_result["score_inputs_returncode"] = returncode
    test_result["score_inputs_failed_suite"] = bool(failed_suite)
    test_result["score_inputs_baseline_keys"] = sorted(list(baseline_for_type.keys())) if isinstance(baseline_for_type, dict) else []

    if test_type in {"functional", "robustness"}:
        return (passed / total) if total > 0 else 0.0

    if test_type == "security":
        gen_metrics = test_result.get("metrics") or {}
        b = _get_baseline_metric(baseline_for_type, "high_risk_count")
        g = _as_float(gen_metrics.get("high_risk_count"))

        test_result["score_inputs_baseline_high_risk_count"] = b
        test_result["score_inputs_generated_high_risk_count"] = g

        if b is None or g is None or b < 0.0 or g < 0.0:
            return 0.0
        if b == 0.0 and g == 0.0:
            return 1.0
        return min(1.0, float(b + 1.0) / float(g + 1.0))

    if test_type == "maintainability":
        gen_metrics = test_result.get("metrics") or {}
        b = _get_baseline_metric(baseline_for_type, "mi_min")
        g = _as_float(gen_metrics.get("mi_min"))

        test_result["score_inputs_baseline_mi_min"] = b
        test_result["score_inputs_generated_mi_min"] = g

        if b is None or g is None or b <= 0.0 or g < 0.0:
            return 0.0

        ratio = float(g) / float(b)
        test_result["score_inputs_ratio_g_over_b"] = ratio
        return _smooth_compress_ratio(ratio)

    if test_type == "performance":
        baseline_time = _get_baseline_metric(baseline_for_type, "performance_suite_time_s")
        actual_time = _as_float(test_result.get("elapsed_time_s"))

        test_result["score_inputs_baseline_time_s"] = baseline_time
        test_result["score_inputs_actual_time_s"] = actual_time

        if failed_suite:
            return 0.0
        if baseline_time is None or actual_time is None or baseline_time <= 0.0 or actual_time <= 0.0:
            return 0.0
        return min(1.0, float(baseline_time) / float(actual_time))

    if test_type == "resource":
        baseline_mem = _get_baseline_metric(baseline_for_type, "avg_memory_mb")
        baseline_cpu = _get_baseline_metric(baseline_for_type, "avg_cpu_percent")
        actual_mem = _as_float(test_result.get("avg_memory_mb"))
        actual_cpu = _as_float(test_result.get("avg_cpu_percent"))

        test_result["score_inputs_baseline_mem_mb"] = baseline_mem
        test_result["score_inputs_baseline_cpu_pct"] = baseline_cpu
        test_result["score_inputs_actual_mem_mb"] = actual_mem
        test_result["score_inputs_actual_cpu_pct"] = actual_cpu

        if failed_suite:
            return 0.0

        if baseline_mem is None or actual_mem is None or baseline_mem <= 0.0 or actual_mem <= 0.0:
            return 0.0

        s_mem = min(1.0, float(baseline_mem) / float(actual_mem))

        if baseline_cpu is None or actual_cpu is None or baseline_cpu <= 0.0 or actual_cpu <= 0.0:
            return float(s_mem)

        s_cpu = min(1.0, float(baseline_cpu) / float(actual_cpu))
        return float((s_mem + s_cpu) / 2.0)

    return 0.0


def run_all_tests(task_file: Path, generated_repo: Path, output_file: Path) -> Dict[str, Any]:
    config = load_task_config(task_file)
    baseline_metrics = config.get("baseline_metrics", {}) or {}
    test_suite = config.get("test_suite", {}) or {}

    timeouts = config.get("suite_timeouts_s", {}) or {}
    default_timeout = float(timeouts.get("default", 60))

    project_name = task_file.parent.name
    target_env_var = f"{project_name.upper()}_TARGET"

    package_name = None
    try:
        package_name = (config.get("package") or {}).get("name")
    except Exception:
        package_name = None

    results: Dict[str, Any] = {}
    scores: Dict[str, float] = {}

    logs_dir = ROOT / "results" / project_name / "pytest_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    for test_type in TEST_TYPES:
        test_path = test_suite.get(test_type)
        if not test_path:
            continue

        test_full_path = _resolve_test_path(project_name, str(test_path))
        if not test_full_path.exists():
            results[test_type] = {
                "error": f"Test file not found: {test_full_path}",
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "total": 1,
                "elapsed_time_s": 0.0,
                "avg_memory_mb": 0.0,
                "avg_cpu_percent": 0.0,
            }
            scores[test_type] = 0.0
            continue

        timeout_s = float(timeouts.get(test_type, default_timeout))
        log_file = logs_dir / f"{test_type}.log"
        add_s = test_type in {"security", "maintainability"}

        print(f"Running {project_name}:{test_type} -> {test_full_path} (timeout={timeout_s}s)")
        test_result = run_test_suite(
            test_path=test_full_path,
            repo_root=generated_repo,
            target_env_var=target_env_var,
            target_value="generated",
            timeout_s=timeout_s,
            log_file=log_file,
            package_name=package_name,
            add_s=add_s,
        )
        results[test_type] = test_result
        scores[test_type] = calculate_score(test_type, test_result, baseline_metrics)

    functional_score = float(scores.get("functional", 0.0) or 0.0)

    nf_weight_sum = sum(float(NON_FUNCTIONAL_WEIGHTS.get(t, 0.0) or 0.0) for t in _NON_TYPES)
    if nf_weight_sum <= 0.0:
        non_functional_score = 0.0
    else:
        non_functional_score = sum(
            float(NON_FUNCTIONAL_WEIGHTS.get(t, 0.0) or 0.0) * float(scores.get(t, 0.0) or 0.0)
            for t in _NON_TYPES
        ) / nf_weight_sum

    non_functional_subscores = {t: round(float(scores.get(t, 0.0) or 0.0), 4) for t in _NON_TYPES}

    output = {
        "project_name": project_name,
        "task_file": str(task_file),
        "generated_repo": str(generated_repo),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "functional_score": round(functional_score, 4),
        "non_functional_score": round(float(non_functional_score), 4),
        "non_functional_subscores": non_functional_subscores,
        "non_functional_weights": NON_FUNCTIONAL_WEIGHTS,
        "results": results,
        "baseline_metrics": baseline_metrics,
        "pytest_logs_dir": str(logs_dir),
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(output, f, allow_unicode=True, sort_keys=False)

    print(f"Wrote results to: {output_file}")
    print(f"Functional score: {functional_score:.4f}")
    print(f"Non-functional score: {float(non_functional_score):.4f}")
    print("Non-functional subscores:")
    for k in ["maintainability", "security", "robustness", "performance", "resource"]:
        if k in non_functional_subscores:
            print(f"  {k}: {float(non_functional_subscores[k]):.4f}")

    return output
