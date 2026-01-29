
"""
Confidence experiments for RAL-Bench / RealAppCodeBench style evaluation.

Implements three validations over FIXED generated repositories (no regeneration):
  1) Stability across reruns (same model, same task, same environment).
  2) Sensitivity to test budget (subsampling functional & robustness tests).
  3) Robustness to noise (idle vs. synthetic CPU load).

Outputs:
  - reruns_details.csv / reruns_summary.csv
  - budget_details.csv / budget_summary.csv
  - noise_details.csv / noise_summary.csv
  - report.md (high-level summary)

Usage (examples):
  # Auto-discover models from generated_root (subfolders)
  python -m evaluation.confidence_experiments \
    --tasks-dir tasks \
    --generated-root generation \
    --out-dir results/confidence \
    --reruns 5 \
    --budget-ratios 0.25 0.5 0.75 1.0 \
    --budget-repeats 30 \
    --noise-repeats 8 \
    --noise-cores 2 \
    --noise-mode cpu

  # If your repo layout differs, provide a template:
  #   {model} and {project} placeholders are supported.
  python -m evaluation.confidence_experiments \
    --tasks-dir tasks \
    --generated-root generation \
    --repo-template "{generated_root}/{model}/{project}" \
    --models "GPT-5.2" "Gemini-3-Pro-preview" \
    --out-dir results/confidence
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import random
import statistics
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import yaml

# Robust import: supports BOTH
#   1) python -m evaluation.confidence_experiments
#   2) python evaluation/confidence_experiments.py
try:
    from . import measure_generated as mg  # type: ignore
except Exception:  # pragma: no cover
    import evaluation.measure_generated as mg  # type: ignore


ROOT = Path(__file__).resolve().parents[1]


# ----------------------------
# Utilities
# ----------------------------

def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _safe_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return default
        return int(x)
    except Exception:
        return default


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    ensure_dir(path.parent)
    if not rows:
        # still write headerless file to indicate completion
        path.write_text("", encoding="utf-8")
        return
    if fieldnames is None:
        # stable order: keys of first row, then any extra keys sorted
        base = list(rows[0].keys())
        extra = sorted({k for r in rows for k in r.keys()} - set(base))
        fieldnames = base + extra
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def percentile(xs: Sequence[float], p: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * p
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    if lo == hi:
        return s[lo]
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def ranks_desc(values: Dict[str, float]) -> Dict[str, float]:
    """
    Dense ranking with average rank for ties, higher value -> better (rank 1).
    Returns mapping key -> rank (float).
    """
    items = sorted(values.items(), key=lambda kv: (-kv[1], kv[0]))
    ranks: Dict[str, float] = {}
    i = 0
    while i < len(items):
        j = i
        while j < len(items) and items[j][1] == items[i][1]:
            j += 1
        # average rank in [i+1, j]
        avg = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[items[k][0]] = avg
        i = j
    return ranks


def spearman_rho(rank_a: Dict[str, float], rank_b: Dict[str, float]) -> float:
    keys = sorted(set(rank_a.keys()) & set(rank_b.keys()))
    n = len(keys)
    if n < 2:
        return 1.0
    ra = [rank_a[k] for k in keys]
    rb = [rank_b[k] for k in keys]
    ma = statistics.mean(ra)
    mb = statistics.mean(rb)
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    den_a = math.sqrt(sum((x - ma) ** 2 for x in ra))
    den_b = math.sqrt(sum((x - mb) ** 2 for x in rb))
    if den_a == 0.0 or den_b == 0.0:
        return 1.0
    return num / (den_a * den_b)


def top1(values: Dict[str, float]) -> Optional[str]:
    if not values:
        return None
    return max(values.items(), key=lambda kv: (kv[1], kv[0]))[0]


def pairwise_flip_rate(order_ref: Dict[str, float], order_new: Dict[str, float]) -> float:
    """
    Fraction of model pairs whose relative order flips between two score maps.
    """
    keys = sorted(set(order_ref.keys()) & set(order_new.keys()))
    if len(keys) < 2:
        return 0.0
    flips = 0
    total = 0
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            ref = order_ref[a] - order_ref[b]
            new = order_new[a] - order_new[b]
            if ref == 0 or new == 0:
                # ignore ties to avoid inflating flips
                continue
            total += 1
            if (ref > 0) != (new > 0):
                flips += 1
    return (flips / total) if total else 0.0


# ----------------------------
# Discovery helpers
# ----------------------------

def discover_tasks(tasks_dir: Path) -> List[Path]:
    return sorted(tasks_dir.glob("*/**/*.yaml"))


def discover_models(generated_root: Path, models: Optional[List[str]]) -> List[str]:
    if models:
        return models
    if not generated_root.exists():
        return []
    return sorted([p.name for p in generated_root.iterdir() if p.is_dir()])


def find_generated_repo(
    generated_root: Path,
    model: str,
    project: str,
    repo_template: Optional[str],
) -> Optional[Path]:
    # Explicit template wins
    if repo_template:
        s = repo_template.format(
            generated_root=str(generated_root),
            model=model,
            project=project,
        )
        p = Path(s).expanduser().resolve()
        if p.exists() and p.is_dir():
            return p

    # Heuristics (common layouts)
    candidates = [
        generated_root / model / project,
        generated_root / project / model,
        generated_root / model / project.lower(),
        generated_root / model / project.replace("-", "_"),
        generated_root / model / project.replace("_", "-"),
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c

    # Last resort: fuzzy search under model dir
    model_dir = generated_root / model
    if model_dir.exists() and model_dir.is_dir():
        for c in model_dir.iterdir():
            if c.is_dir() and c.name.lower() == project.lower():
                return c
    return None


# ----------------------------
# Pytest nodeid sampling (for budget sensitivity)
# ----------------------------

def _build_pytest_env(
    repo_root: Path,
    project_name: str,
    package_name: Optional[str],
    target_value: str = "generated",
) -> Dict[str, str]:
    env = os.environ.copy()
    target_env_var = f"{project_name.upper()}_TARGET"
    env[target_env_var] = target_value
    env[mg.REPO_ROOT_ENV] = str(repo_root)
    if package_name:
        env[mg.PKG_NAME_ENV] = package_name

    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(repo_root) + (os.pathsep + existing_pp if existing_pp else "")
    return env


def collect_nodeids(test_path: Path, repo_root: Path, project_name: str, package_name: Optional[str]) -> List[str]:
    env = _build_pytest_env(repo_root, project_name, package_name)
    cmd = [os.environ.get("PYTHON", "python"), "-m", "pytest", str(test_path), "--collect-only", "-q"]
    out = subprocess.check_output(cmd, cwd=str(ROOT), env=env, text=True, stderr=subprocess.STDOUT)
    nodeids: List[str] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        # typical output: tests/foo_test.py::test_x
        if "::" in line and not line.startswith("<"):
            nodeids.append(line)
    # de-dup keep order
    seen = set()
    uniq = []
    for n in nodeids:
        if n not in seen:
            seen.add(n)
            uniq.append(n)
    return uniq


def run_pytest_nodeids(
    nodeids: List[str],
    repo_root: Path,
    project_name: str,
    package_name: Optional[str],
    timeout_s: float,
) -> Dict[str, Any]:
    """
    Run pytest for specific nodeids; parse passed/failed/total using mg._parse_pytest_counts.
    Note: For budget sensitivity we only need counts, not time/mem/cpu.
    """
    env = _build_pytest_env(repo_root, project_name, package_name)
    cmd = [os.environ.get("PYTHON", "python"), "-m", "pytest"] + nodeids + ["-q"]
    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_s,
            check=False,
        )
        output = proc.stdout or ""
        counts = mg._parse_pytest_counts(output)  # type: ignore
        return {
            **counts,
            "returncode": proc.returncode,
            "elapsed_time_s": time.time() - start,
            "raw_output": output,
        }
    except subprocess.TimeoutExpired as e:
        output = (e.stdout or "") if hasattr(e, "stdout") else ""
        counts = mg._parse_pytest_counts(output)  # type: ignore
        # mark as failed suite
        return {
            **counts,
            "returncode": 124,
            "elapsed_time_s": timeout_s,
            "raw_output": output,
            "error": "timeout",
        }


# ----------------------------
# Noise generator
# ----------------------------

def cpu_burn(duration_s: float) -> None:
    # busy loop
    end = time.time() + duration_s
    x = 0.0
    while time.time() < end:
        x = (x + 1.234567) * 0.999999
    _ = x


def spawn_noise(mode: str, duration_s: float, cores: int) -> List[subprocess.Popen]:
    """
    Spawn synthetic noise. For portability, we spawn Python processes doing CPU burn.
    """
    procs: List[subprocess.Popen] = []
    if mode == "none":
        return procs
    if mode == "cpu":
        # spawn N python processes each running a burn loop
        for _ in range(max(1, cores)):
            cmd = [os.environ.get("PYTHON", "python"), "-c", f"import time\nx=0.0\nend=time.time()+{duration_s}\n"
                                                            f"import math\n"
                                                            f"while time.time()<end:\n"
                                                            f"  x=(x+1.234567)*0.999999\n"
                                                            f"print(x)\n"]
            # stdout suppressed
            p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            procs.append(p)
    return procs


def kill_noise(procs: List[subprocess.Popen]) -> None:
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
    for p in procs:
        try:
            p.wait(timeout=2)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass


# ----------------------------
# Core experiment runners
# ----------------------------

@dataclass
class RunResult:
    functional: float
    non_functional: float
    subscores: Dict[str, float]
    raw: Dict[str, Any]


def run_full_once(task_yaml: Path, repo_root: Path, out_yaml: Path) -> Dict[str, Any]:
    ensure_dir(out_yaml.parent)
    return mg.run_all_tests(task_yaml, repo_root, out_yaml)


def extract_run_result(full_output: Dict[str, Any]) -> RunResult:
    subs = full_output.get("non_functional_subscores", {}) or {}
    # raw signals by suite
    raw: Dict[str, Any] = {}
    results = full_output.get("results", {}) or {}
    for t, r in results.items():
        if not isinstance(r, dict):
            continue
        if t in {"performance"}:
            raw["perf_elapsed_time_s"] = r.get("elapsed_time_s")
        if t in {"resource"}:
            raw["avg_memory_mb"] = r.get("avg_memory_mb")
            raw["avg_cpu_percent"] = r.get("avg_cpu_percent")
        if t in {"security"}:
            raw["high_risk_count"] = r.get("high_risk_count")
        if t in {"maintainability"}:
            raw["mi_min"] = r.get("mi_min")
        if t in {"robustness"}:
            raw["robust_passed"] = r.get("passed")
            raw["robust_total"] = r.get("total")
    return RunResult(
        functional=_safe_float(full_output.get("functional_score")),
        non_functional=_safe_float(full_output.get("non_functional_score")),
        subscores={k: _safe_float(v) for k, v in subs.items()},
        raw=raw,
    )


def compute_nf_from_subscores(subscores: Dict[str, float]) -> float:
    ws = 0.0
    s = 0.0
    for k in ["maintainability", "security", "robustness", "performance", "resource"]:
        w = float(mg.NON_FUNCTIONAL_WEIGHTS.get(k, 0.0) or 0.0)
        ws += w
        s += w * float(subscores.get(k, 0.0) or 0.0)
    return (s / ws) if ws > 0 else 0.0


def stability_across_reruns(
    tasks: List[Path],
    models: List[str],
    generated_root: Path,
    repo_template: Optional[str],
    out_dir: Path,
    reruns: int,
    seed: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[Tuple[str, str], RunResult]]:
    """
    Returns:
      - details_rows (one row per run)
      - summary_rows (mean/std/cv per (model, project))
      - full_mean_cache[(model, project)] = RunResult(mean over runs)  (for later experiments)
    """
    random.seed(seed)
    details: List[Dict[str, Any]] = []
    summary: List[Dict[str, Any]] = []
    mean_cache: Dict[Tuple[str, str], RunResult] = {}

    for task_yaml in tasks:
        project = task_yaml.parent.name
        config = mg.load_task_config(task_yaml)
        package_name = None
        try:
            package_name = (config.get("package") or {}).get("name")
        except Exception:
            package_name = None

        for model in models:
            repo = find_generated_repo(generated_root, model, project, repo_template)
            if repo is None:
                details.append({
                    "phase": "reruns",
                    "project": project,
                    "model": model,
                    "run": -1,
                    "error": "generated_repo_not_found",
                })
                continue

            run_results: List[RunResult] = []
            for r in range(reruns):
                out_yaml = out_dir / "reruns" / model / project / f"run_{r+1:02d}.yaml"
                full_out = run_full_once(task_yaml, repo, out_yaml)
                rr = extract_run_result(full_out)
                run_results.append(rr)

                row = {
                    "phase": "reruns",
                    "project": project,
                    "model": model,
                    "run": r + 1,
                    "functional_score": rr.functional,
                    "non_functional_score": rr.non_functional,
                    "maintainability": rr.subscores.get("maintainability", 0.0),
                    "security": rr.subscores.get("security", 0.0),
                    "robustness": rr.subscores.get("robustness", 0.0),
                    "performance": rr.subscores.get("performance", 0.0),
                    "resource": rr.subscores.get("resource", 0.0),
                    "perf_elapsed_time_s": _safe_float(rr.raw.get("perf_elapsed_time_s"), 0.0),
                    "avg_memory_mb": _safe_float(rr.raw.get("avg_memory_mb"), 0.0),
                    "avg_cpu_percent": _safe_float(rr.raw.get("avg_cpu_percent"), 0.0),
                    "high_risk_count": _safe_int(rr.raw.get("high_risk_count"), 0),
                    "mi_min": _safe_float(rr.raw.get("mi_min"), 0.0),
                    "robust_passed": _safe_int(rr.raw.get("robust_passed"), 0),
                    "robust_total": _safe_int(rr.raw.get("robust_total"), 0),
                    "repo_path": str(repo),
                    "task_yaml": str(task_yaml),
                    "package_name": package_name or "",
                }
                details.append(row)

            # summary stats
            if not run_results:
                continue

            def series(getter) -> List[float]:
                return [float(getter(x)) for x in run_results]

            metrics = {
                "functional_score": series(lambda x: x.functional),
                "non_functional_score": series(lambda x: x.non_functional),
                "maintainability": series(lambda x: x.subscores.get("maintainability", 0.0)),
                "security": series(lambda x: x.subscores.get("security", 0.0)),
                "robustness": series(lambda x: x.subscores.get("robustness", 0.0)),
                "performance": series(lambda x: x.subscores.get("performance", 0.0)),
                "resource": series(lambda x: x.subscores.get("resource", 0.0)),
                "perf_elapsed_time_s": series(lambda x: _safe_float(x.raw.get("perf_elapsed_time_s"), 0.0)),
                "avg_memory_mb": series(lambda x: _safe_float(x.raw.get("avg_memory_mb"), 0.0)),
                "avg_cpu_percent": series(lambda x: _safe_float(x.raw.get("avg_cpu_percent"), 0.0)),
                "mi_min": series(lambda x: _safe_float(x.raw.get("mi_min"), 0.0)),
            }

            sum_row: Dict[str, Any] = {"phase": "reruns", "project": project, "model": model, "reruns": reruns}
            for k, xs in metrics.items():
                m = statistics.mean(xs) if xs else 0.0
                sd = statistics.pstdev(xs) if len(xs) >= 2 else 0.0
                cv = (sd / m) if m != 0.0 else 0.0
                sum_row[f"{k}_mean"] = m
                sum_row[f"{k}_std"] = sd
                sum_row[f"{k}_cv"] = cv
                sum_row[f"{k}_p05"] = percentile(xs, 0.05) if xs else 0.0
                sum_row[f"{k}_p95"] = percentile(xs, 0.95) if xs else 0.0
            summary.append(sum_row)

            # mean cache for later (use mean subscores)
            mean_sub = {k: _safe_float(sum_row.get(f"{k}_mean", 0.0)) for k in ["maintainability", "security", "robustness", "performance", "resource"]}
            mean_nf = _safe_float(sum_row.get("non_functional_score_mean", 0.0))
            mean_func = _safe_float(sum_row.get("functional_score_mean", 0.0))
            mean_cache[(model, project)] = RunResult(
                functional=mean_func,
                non_functional=mean_nf,
                subscores=mean_sub,
                raw={
                    "perf_elapsed_time_s": _safe_float(sum_row.get("perf_elapsed_time_s_mean", 0.0)),
                    "avg_memory_mb": _safe_float(sum_row.get("avg_memory_mb_mean", 0.0)),
                    "avg_cpu_percent": _safe_float(sum_row.get("avg_cpu_percent_mean", 0.0)),
                    "mi_min": _safe_float(sum_row.get("mi_min_mean", 0.0)),
                },
            )

    return details, summary, mean_cache


def sensitivity_to_test_budget(
    tasks: List[Path],
    models: List[str],
    generated_root: Path,
    repo_template: Optional[str],
    out_dir: Path,
    mean_cache: Dict[Tuple[str, str], RunResult],
    ratios: List[float],
    repeats: int,
    seed: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Subsample functional+robustness tests by nodeid and evaluate stability of rankings.

    Uses mean_cache to keep other NF subscores fixed (maint/security/perf/resource) and only
    recompute robustness subscore under subsampling to produce a budgeted NF score.

    Returns:
      - budget_details rows: per (project, model, ratio, rep)
      - budget_summary rows: per (project, ratio): rank correlation, top1 stability, flip rate
    """
    random.seed(seed)
    details: List[Dict[str, Any]] = []
    summary: List[Dict[str, Any]] = []

    # Pre-collect nodeids per (project, model) to ensure the subset is valid in that repo.
    # Note: nodeids may differ slightly across repos due to import/executability issues.
    nodeids_cache: Dict[Tuple[str, str, str], List[str]] = {}  # (project, model, test_type) -> nodeids

    for task_yaml in tasks:
        project = task_yaml.parent.name
        cfg = mg.load_task_config(task_yaml)
        test_suite = cfg.get("test_suite", {}) or {}
        timeouts = cfg.get("suite_timeouts_s", {}) or {}
        default_timeout = float(timeouts.get("default", 60))

        package_name = None
        try:
            package_name = (cfg.get("package") or {}).get("name")
        except Exception:
            package_name = None

        func_path = test_suite.get("functional")
        rob_path = test_suite.get("robustness")
        if not func_path or not rob_path:
            continue

        func_test = mg._resolve_test_path(project, str(func_path))  # type: ignore
        rob_test = mg._resolve_test_path(project, str(rob_path))    # type: ignore

        for model in models:
            repo = find_generated_repo(generated_root, model, project, repo_template)
            if repo is None:
                continue

            # Collect nodeids for this repo (functional + robustness)
            for ttype, tfile in [("functional", func_test), ("robustness", rob_test)]:
                key = (project, model, ttype)
                if key in nodeids_cache:
                    continue
                try:
                    nodeids_cache[key] = collect_nodeids(tfile, repo, project, package_name)
                except Exception as e:
                    nodeids_cache[key] = []
                    details.append({
                        "phase": "budget",
                        "project": project,
                        "model": model,
                        "ratio": -1,
                        "rep": -1,
                        "error": f"collect_nodeids_failed:{e}",
                    })

        # For each ratio & rep: compute scores for all models then assess ranking stability.
        # Reference ranking: mean functional (full) and mean budgeted NF at ratio=1.0 from mean_cache.
        ref_func_scores = {m: mean_cache.get((m, project), RunResult(0, 0, {}, {})).functional for m in models}
        ref_nf_scores = {m: mean_cache.get((m, project), RunResult(0, 0, {}, {})).non_functional for m in models}
        ref_rank_func = ranks_desc(ref_func_scores)
        ref_rank_nf = ranks_desc(ref_nf_scores)
        ref_top1_nf = top1(ref_nf_scores)

        for ratio in ratios:
            # accumulate per-rep ranking stats
            rhos_nf: List[float] = []
            top1_hits: int = 0
            flip_rates: List[float] = []

            for rep in range(repeats):
                sampled_nf_scores: Dict[str, float] = {}
                sampled_func_scores: Dict[str, float] = {}

                for model in models:
                    repo = find_generated_repo(generated_root, model, project, repo_template)
                    if repo is None:
                        continue

                    func_nodeids = nodeids_cache.get((project, model, "functional"), [])
                    rob_nodeids = nodeids_cache.get((project, model, "robustness"), [])
                    if not func_nodeids or not rob_nodeids:
                        # treat as 0
                        s_func = 0.0
                        s_rob = 0.0
                    else:
                        kf = max(1, int(round(ratio * len(func_nodeids))))
                        kr = max(1, int(round(ratio * len(rob_nodeids))))
                        sf = random.sample(func_nodeids, min(kf, len(func_nodeids)))
                        sr = random.sample(rob_nodeids, min(kr, len(rob_nodeids)))

                        tr_func = run_pytest_nodeids(
                            sf, repo, project, package_name,
                            timeout_s=float(timeouts.get("functional", default_timeout)),
                        )
                        s_func = float(mg.calculate_score("functional", tr_func, cfg.get("baseline_metrics", {}) or {}))

                        tr_rob = run_pytest_nodeids(
                            sr, repo, project, package_name,
                            timeout_s=float(timeouts.get("robustness", default_timeout)),
                        )
                        s_rob = float(mg.calculate_score("robustness", tr_rob, cfg.get("baseline_metrics", {}) or {}))

                    # NF budgeted: keep other subscores fixed from mean_cache; replace robustness
                    base = mean_cache.get((model, project))
                    if base is None:
                        subs = {"maintainability": 0.0, "security": 0.0, "robustness": 0.0, "performance": 0.0, "resource": 0.0}
                    else:
                        subs = dict(base.subscores)
                    subs["robustness"] = float(s_rob)
                    nf_budget = compute_nf_from_subscores(subs)

                    sampled_func_scores[model] = float(s_func)
                    sampled_nf_scores[model] = float(nf_budget)

                    details.append({
                        "phase": "budget",
                        "project": project,
                        "model": model,
                        "ratio": ratio,
                        "rep": rep + 1,
                        "sampled_func": float(s_func),
                        "sampled_robust": float(s_rob),
                        "budgeted_nf": float(nf_budget),
                        "ref_func_full_mean": float(ref_func_scores.get(model, 0.0)),
                        "ref_nf_full_mean": float(ref_nf_scores.get(model, 0.0)),
                        "func_tests_total": len(nodeids_cache.get((project, model, "functional"), [])),
                        "rob_tests_total": len(nodeids_cache.get((project, model, "robustness"), [])),
                    })

                # ranking stability (NF)
                rho = spearman_rho(ref_rank_nf, ranks_desc(sampled_nf_scores))
                rhos_nf.append(rho)

                t1 = top1(sampled_nf_scores)
                if ref_top1_nf is not None and t1 == ref_top1_nf:
                    top1_hits += 1

                flip_rates.append(pairwise_flip_rate(ref_nf_scores, sampled_nf_scores))

            summary.append({
                "phase": "budget",
                "project": project,
                "ratio": ratio,
                "repeats": repeats,
                "nf_rank_spearman_mean": statistics.mean(rhos_nf) if rhos_nf else 0.0,
                "nf_rank_spearman_p05": percentile(rhos_nf, 0.05) if rhos_nf else 0.0,
                "nf_rank_spearman_p95": percentile(rhos_nf, 0.95) if rhos_nf else 0.0,
                "nf_top1_stability": (top1_hits / repeats) if repeats > 0 else 0.0,
                "pairwise_flip_rate_mean": statistics.mean(flip_rates) if flip_rates else 0.0,
                "pairwise_flip_rate_p95": percentile(flip_rates, 0.95) if flip_rates else 0.0,
            })

    return details, summary


def robustness_to_noise(
    tasks: List[Path],
    models: List[str],
    generated_root: Path,
    repo_template: Optional[str],
    out_dir: Path,
    repeats: int,
    noise_mode: str,
    noise_cores: int,
    seed: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Idle vs. noisy runs for performance/resource suites; evaluate whether rankings flip.

    Returns:
      - noise_details: per (project, model, condition, rep)
      - noise_summary: per project: rank correlations idle vs noisy, top1 flips
    """
    random.seed(seed)
    details: List[Dict[str, Any]] = []
    summary: List[Dict[str, Any]] = []

    for task_yaml in tasks:
        project = task_yaml.parent.name
        cfg = mg.load_task_config(task_yaml)
        test_suite = cfg.get("test_suite", {}) or {}
        baseline_metrics = cfg.get("baseline_metrics", {}) or {}
        timeouts = cfg.get("suite_timeouts_s", {}) or {}
        default_timeout = float(timeouts.get("default", 60))

        package_name = None
        try:
            package_name = (cfg.get("package") or {}).get("name")
        except Exception:
            package_name = None

        perf_path = test_suite.get("performance")
        res_path = test_suite.get("resource")
        if not perf_path and not res_path:
            continue

        perf_test = mg._resolve_test_path(project, str(perf_path)) if perf_path else None  # type: ignore
        res_test = mg._resolve_test_path(project, str(res_path)) if res_path else None    # type: ignore

        # Run two conditions: idle, noisy
        cond_to_scores: Dict[str, Dict[str, float]] = {"idle": {}, "noisy": {}}

        for cond in ["idle", "noisy"]:
            for model in models:
                repo = find_generated_repo(generated_root, model, project, repo_template)
                if repo is None:
                    continue

                perfs: List[float] = []
                ress: List[float] = []

                for rep in range(repeats):
                    # spawn noise for the whole suite run
                    dur = float(timeouts.get("performance", default_timeout)) if perf_test else 0.0
                    dur = max(dur, float(timeouts.get("resource", default_timeout)) if res_test else 0.0)
                    dur = max(dur, 30.0)  # ensure the load lasts through the run

                    procs: List[subprocess.Popen] = []
                    try:
                        if cond == "noisy":
                            procs = spawn_noise(noise_mode, duration_s=dur, cores=noise_cores)

                        if perf_test:
                            tr = mg.run_test_suite(
                                test_path=perf_test,
                                repo_root=repo,
                                target_env_var=f"{project.upper()}_TARGET",
                                target_value="generated",
                                timeout_s=float(timeouts.get("performance", default_timeout)),
                                log_file=None,
                                package_name=package_name,
                                add_s=False,
                            )
                            s = float(mg.calculate_score("performance", tr, baseline_metrics))
                            perfs.append(s)
                            details.append({
                                "phase": "noise",
                                "project": project,
                                "model": model,
                                "condition": cond,
                                "rep": rep + 1,
                                "metric": "performance",
                                "score": s,
                                "elapsed_time_s": _safe_float(tr.get("elapsed_time_s"), 0.0),
                                "returncode": _safe_int(tr.get("returncode"), 1),
                            })

                        if res_test:
                            tr = mg.run_test_suite(
                                test_path=res_test,
                                repo_root=repo,
                                target_env_var=f"{project.upper()}_TARGET",
                                target_value="generated",
                                timeout_s=float(timeouts.get("resource", default_timeout)),
                                log_file=None,
                                package_name=package_name,
                                add_s=False,
                            )
                            s = float(mg.calculate_score("resource", tr, baseline_metrics))
                            ress.append(s)
                            details.append({
                                "phase": "noise",
                                "project": project,
                                "model": model,
                                "condition": cond,
                                "rep": rep + 1,
                                "metric": "resource",
                                "score": s,
                                "avg_memory_mb": _safe_float(tr.get("avg_memory_mb"), 0.0),
                                "avg_cpu_percent": _safe_float(tr.get("avg_cpu_percent"), 0.0),
                                "returncode": _safe_int(tr.get("returncode"), 1),
                            })
                    finally:
                        if procs:
                            kill_noise(procs)

                # aggregate: use mean score across repeats (you can switch to median if desired)
                agg = 0.0
                parts = 0
                if perfs:
                    agg += statistics.mean(perfs)
                    parts += 1
                if ress:
                    agg += statistics.mean(ress)
                    parts += 1
                cond_to_scores[cond][model] = (agg / parts) if parts else 0.0

        # ranking comparison idle vs noisy
        idle_scores = cond_to_scores["idle"]
        noisy_scores = cond_to_scores["noisy"]
        rho = spearman_rho(ranks_desc(idle_scores), ranks_desc(noisy_scores))
        top_idle = top1(idle_scores)
        top_noisy = top1(noisy_scores)
        flip = 1 if (top_idle is not None and top_noisy is not None and top_idle != top_noisy) else 0
        pw_flip = pairwise_flip_rate(idle_scores, noisy_scores)

        summary.append({
            "phase": "noise",
            "project": project,
            "repeats": repeats,
            "noise_mode": noise_mode,
            "noise_cores": noise_cores,
            "rank_spearman_idle_vs_noisy": rho,
            "top1_idle": top_idle or "",
            "top1_noisy": top_noisy or "",
            "top1_flipped": flip,
            "pairwise_flip_rate": pw_flip,
        })

    return details, summary


# ----------------------------
# Reporting
# ----------------------------

def build_report(
    out_dir: Path,
    rerun_summary: List[Dict[str, Any]],
    budget_summary: List[Dict[str, Any]],
    noise_summary: List[Dict[str, Any]],
) -> str:
    lines: List[str] = []
    lines.append("# Confidence Experiments Report\n")

    # Rerun stability (aggregate CV)
    cvs_nf = [float(r.get("non_functional_score_cv", 0.0)) for r in rerun_summary if r.get("phase") == "reruns"]
    cvs_perf = [float(r.get("performance_cv", 0.0)) for r in rerun_summary if r.get("phase") == "reruns"]
    cvs_res = [float(r.get("resource_cv", 0.0)) for r in rerun_summary if r.get("phase") == "reruns"]

    def agg_stats(xs: List[float]) -> str:
        if not xs:
            return "n/a"
        return f"mean={statistics.mean(xs):.4f}, p95={percentile(xs,0.95):.4f}, max={max(xs):.4f}"

    lines.append("## 1) Stability Across Reruns\n")
    lines.append(f"- Non-functional score CV: {agg_stats(cvs_nf)}\n")
    lines.append(f"- Performance subscore CV: {agg_stats(cvs_perf)}\n")
    lines.append(f"- Resource subscore CV: {agg_stats(cvs_res)}\n")

    # Budget sensitivity
    lines.append("## 2) Sensitivity to Test Budget (Functional/Robustness Subsampling)\n")
    # group by ratio
    by_ratio: Dict[float, List[float]] = {}
    for r in budget_summary:
        ratio = float(r.get("ratio", 0.0))
        by_ratio.setdefault(ratio, []).append(float(r.get("nf_rank_spearman_mean", 0.0)))
    for ratio in sorted(by_ratio.keys()):
        xs = by_ratio[ratio]
        lines.append(f"- ratio={ratio:.2f}: mean Spearman( NF ranks )={statistics.mean(xs):.4f}, p05={percentile(xs,0.05):.4f}\n")

    # Noise robustness
    lines.append("## 3) Robustness to Noise (Idle vs Synthetic CPU Load)\n")
    rhos = [float(r.get("rank_spearman_idle_vs_noisy", 0.0)) for r in noise_summary]
    flips = sum(int(r.get("top1_flipped", 0)) for r in noise_summary)
    lines.append(f"- Spearman(rank idle vs noisy): {agg_stats(rhos)}\n")
    lines.append(f"- Top-1 flips across projects: {flips}/{len(noise_summary)}\n")

    return "".join(lines)


# ----------------------------
# Main
# ----------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks-dir", default="tasks", help="Tasks directory (contains */**/*.yaml)")
    ap.add_argument("--generated-root", default="generation", help="Root dir containing fixed generated repos")
    ap.add_argument("--out-dir", default="results/confidence", help="Output directory")

    ap.add_argument("--models", nargs="*", default=None, help="Explicit model names (otherwise auto-discover subdirs under generated-root)")
    ap.add_argument("--repo-template", default=None,
                    help="Optional repo path template, e.g., '{generated_root}/{model}/{project}' or '{generated_root}/{project}/{model}'")

    ap.add_argument("--reruns", type=int, default=5, help="Number of reruns for stability")
    ap.add_argument("--seed", type=int, default=1234)

    ap.add_argument("--budget-ratios", nargs="*", type=float, default=[0.25, 0.5, 0.75, 1.0], help="Subsampling ratios")
    ap.add_argument("--budget-repeats", type=int, default=30, help="Repeats per ratio for budget sensitivity")

    ap.add_argument("--noise-repeats", type=int, default=8, help="Repeats per condition for noise experiment")
    ap.add_argument("--noise-mode", choices=["none", "cpu"], default="cpu", help="Noise type (synthetic)")
    ap.add_argument("--noise-cores", type=int, default=2, help="How many CPU burners to spawn")
    ap.add_argument("--tasks-limit", type=int, default=0, help="For debugging: limit number of tasks (0=all)")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    tasks_dir = Path(args.tasks_dir).resolve()
    gen_root = Path(args.generated_root).resolve()
    out_dir = Path(args.out_dir).resolve()

    ensure_dir(out_dir)

    tasks = discover_tasks(tasks_dir)
    if args.tasks_limit and args.tasks_limit > 0:
        tasks = tasks[: args.tasks_limit]

    models = discover_models(gen_root, args.models)
    if not tasks:
        raise SystemExit(f"No tasks found under: {tasks_dir}")
    if not models:
        raise SystemExit(f"No models found. Provide --models or ensure subdirs exist under: {gen_root}")

    # 1) Rerun stability (also builds mean_cache)
    rerun_details, rerun_summary, mean_cache = stability_across_reruns(
        tasks=tasks,
        models=models,
        generated_root=gen_root,
        repo_template=args.repo_template,
        out_dir=out_dir,
        reruns=int(args.reruns),
        seed=int(args.seed),
    )
    write_csv(out_dir / "reruns_details.csv", rerun_details)
    write_csv(out_dir / "reruns_summary.csv", rerun_summary)

    # 2) Budget sensitivity (uses mean_cache)
    budget_details, budget_summary = sensitivity_to_test_budget(
        tasks=tasks,
        models=models,
        generated_root=gen_root,
        repo_template=args.repo_template,
        out_dir=out_dir,
        mean_cache=mean_cache,
        ratios=list(args.budget_ratios),
        repeats=int(args.budget_repeats),
        seed=int(args.seed),
    )
    write_csv(out_dir / "budget_details.csv", budget_details)
    write_csv(out_dir / "budget_summary.csv", budget_summary)

    # 3) Noise robustness (performance/resource under idle vs noisy)
    noise_details, noise_summary = robustness_to_noise(
        tasks=tasks,
        models=models,
        generated_root=gen_root,
        repo_template=args.repo_template,
        out_dir=out_dir,
        repeats=int(args.noise_repeats),
        noise_mode=str(args.noise_mode),
        noise_cores=int(args.noise_cores),
        seed=int(args.seed),
    )
    write_csv(out_dir / "noise_details.csv", noise_details)
    write_csv(out_dir / "noise_summary.csv", noise_summary)

    report = build_report(out_dir, rerun_summary, budget_summary, noise_summary)
    (out_dir / "report.md").write_text(report, encoding="utf-8")

    print(f"[OK] Wrote: {out_dir}")
    print(f"  - reruns_details.csv / reruns_summary.csv")
    print(f"  - budget_details.csv / budget_summary.csv")
    print(f"  - noise_details.csv / noise_summary.csv")
    print(f"  - report.md")


if __name__ == "__main__":
    main()
