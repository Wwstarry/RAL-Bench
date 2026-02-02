import argparse
import subprocess
import yaml
import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"
RESULTS_DIR_DEFAULT = ROOT / "results_m4"


def find_all_tasks():
    return sorted(TASKS_DIR.glob("*/**/*.yaml"))


def run_single_task(task_yaml: Path, model_name: str, skip_generation: bool, generated_root: str, results_root: str, use_task_generated_repo: bool) -> bool:
    cmd = [
        "python",
        "-m",
        "evaluation.run_benchmark_m4",
        "--task",
        str(task_yaml),
        "--generated-root",
        generated_root,
        "--results-root",
        results_root,
    ]

    if skip_generation:
        cmd.append("--skip-generation")

    if use_task_generated_repo:
        cmd.append("--use-task-generated-repo")

    env = os.environ.copy()
    env["RACB_MODEL"] = model_name

    try:
        subprocess.run(cmd, check=True, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[WARN] Task failed: {task_yaml} (exit={e.returncode})")
        return False
    except KeyboardInterrupt:
        print("[WARN] Interrupted by user")
        return False


def load_result_or_default(project: str, results_dir: Path) -> dict:
    result_file = results_dir / f"{project}_results.yaml"
    if not result_file.exists():
        print(f"[WARN] Result file not found for {project}, using zero scores")
        return {
            "functional_score": 0.0,
            "non_functional_score": 0.0,
            "scores": {},
            "non_functional_subscores": {},
        }

    with open(result_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _f(x, default=0.0) -> float:
    try:
        if x is None:
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def main(model_name: str, skip_generation: bool, generated_root: str, results_root: str, use_task_generated_repo: bool):
    results_dir = (ROOT / results_root).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    suffix = "eval_only" if skip_generation else "gen_and_eval"
    csv_path = results_dir / f"{model_name}__m4__{suffix}.csv"

    fieldnames = [
        "model",
        "mode",
        "strategy",
        "project",
        "functional_score",
        "non_functional_score",
        "maintainability",
        "security",
        "robustness",
        "performance",
        "resource",
    ]

    rows = []

    for task_yaml in find_all_tasks():
        project = task_yaml.parent.name
        mode_str = "eval_only" if skip_generation else "gen_and_eval"
        print(f"\n=== Running {project} (M4 | {mode_str}) ===")

        run_single_task(task_yaml, model_name, skip_generation, generated_root, results_root, use_task_generated_repo)

        result = load_result_or_default(project, results_dir)

        scores = result.get("scores", {}) or {}
        nf_sub = result.get("non_functional_subscores", {}) or {}

        def get_sub(k: str) -> float:
            if k in nf_sub:
                return _f(nf_sub.get(k), 0.0)
            return _f(scores.get(k), 0.0)

        rows.append({
            "model": model_name,
            "mode": mode_str,
            "strategy": "m4",
            "project": project,
            "functional_score": _f(result.get("functional_score"), 0.0),
            "non_functional_score": _f(result.get("non_functional_score"), 0.0),
            "maintainability": get_sub("maintainability"),
            "security": get_sub("security"),
            "robustness": get_sub("robustness"),
            "performance": get_sub("performance"),
            "resource": get_sub("resource"),
        })

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nAll M4 results written to: {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--skip-generation", action="store_true")

    # 与 run_benchmark_m4 保持一致的默认隔离目录
    parser.add_argument("--generated-root", default="generation_m4")
    parser.add_argument("--results-root", default="results_m4")

    # 如你确实想沿用 YAML 里的 generated_repository（会覆盖 baseline），显式打开
    parser.add_argument("--use-task-generated-repo", action="store_true")

    args = parser.parse_args()
    main(args.model, args.skip_generation, args.generated_root, args.results_root, args.use_task_generated_repo)
