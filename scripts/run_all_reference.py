"""Validate every pinned reference and refresh its stored baseline metrics."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"


def main() -> int:
    failures: list[str] = []
    task_files = sorted(TASKS_DIR.glob("*/*.yaml"))
    print(f"Found {len(task_files)} task files")

    for task_file in task_files:
        config = yaml.safe_load(task_file.read_text(encoding="utf-8")) or {}
        reference = (ROOT / str(config.get("reference_repository", ""))).resolve()
        if not reference.is_dir():
            failures.append(f"{task_file.relative_to(ROOT).as_posix()}: missing reference repository")
            continue

        project = task_file.parent.name
        command = [
            sys.executable,
            "-m",
            "evaluation.measure_reference",
            str(task_file),
            "--target-env",
            f"{project.upper()}_TARGET",
            "--reference-value",
            "reference",
        ]
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            failures.append(f"{task_file.relative_to(ROOT).as_posix()}: exit {result.returncode}")

    if failures:
        print("Reference validation failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Validated {len(task_files)} reference tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
