# scripts/run_all_reference.py
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

import yaml  # pip install pyyaml


ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"


# 如果 tasks/<Project> 和 repositories/<RepoDir> 不一致，在这里加映射
# 例： "FastAPIUsers": "fastapi-users"
PROJECT_TO_REPO_DIR = {
    # "FastAPIUsers": "fastapi-users",
    # "Cmd2": "cmd2",
}


def guess_target_env(cfg: Dict[str, Any]) -> Optional[str]:
    """
    Try multiple possible keys for target env in yaml.
    """
    for k in ("target_env", "target-env", "targetEnv"):
        v = cfg.get(k)
        if v:
            return str(v)
    return None


def project_name_from_yaml_path(yaml_path: Path) -> str:
    # tasks/<Project>/<file>.yaml -> <Project>
    return yaml_path.parent.name


def repo_dir_for_project(project: str) -> str:
    return PROJECT_TO_REPO_DIR.get(project, project)


def run_measure_reference(yaml_path: Path, target_env: str, repo_root: Optional[Path]) -> int:
    if repo_root and repo_root.exists():
        os.environ[target_env] = str(repo_root.resolve())
        print(f"Set env {target_env}={os.environ[target_env]}")
    else:
        print(f"WARN: repo root not found; will run without setting {target_env} explicitly.")

    cmd = [
        "python",
        str(ROOT / "evaluation" / "measure_reference.py"),
        str(yaml_path),
        "--target-env",
        target_env,
        "--reference-value",
        "reference",
    ]
    r = subprocess.run(cmd)
    return r.returncode


def main() -> None:
    yamls = sorted(TASKS_DIR.rglob("*.yaml"))
    print(f"Found {len(yamls)} yaml files under {TASKS_DIR}")

    failed = []
    skipped = []

    for y in yamls:
        print("=" * 100)
        print("YAML:", y)

        try:
            cfg = yaml.safe_load(y.read_text(encoding="utf-8")) or {}
        except Exception as e:
            print("SKIP: cannot parse yaml:", e)
            skipped.append(str(y))
            continue

        target_env = guess_target_env(cfg)
        if not target_env:
            print("SKIP: missing target_env in yaml")
            skipped.append(str(y))
            continue

        project = project_name_from_yaml_path(y)
        repo_dir = repo_dir_for_project(project)

        # reference 仓库默认放在 ./repositories/<repo_dir>
        repo_root = ROOT / "repositories" / repo_dir
        if not repo_root.exists():
            # 有些项目可能在 repositories 下用不同命名/大小写
            print(f"WARN: repo folder not found at {repo_root}. If needed, add mapping in PROJECT_TO_REPO_DIR.")
            repo_root = None

        code = run_measure_reference(y, target_env, repo_root)
        if code != 0:
            print(f"FAIL: measure_reference exit={code}")
            failed.append(str(y))
        else:
            print("OK: baseline_metrics updated in yaml.")

    print("\n" + "=" * 100)
    print("DONE")
    print(f"Failed: {len(failed)}")
    for f in failed:
        print("  -", f)
    print(f"Skipped: {len(skipped)}")
    for s in skipped:
        print("  -", s)


if __name__ == "__main__":
    main()
