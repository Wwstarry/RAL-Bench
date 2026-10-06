"""Fast structural validation for the paper artifact and Fresh-50 manifest."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SUITES = {"functional", "maintainability", "security", "robustness", "efficiency", "resource"}
LOCAL_PATH = re.compile(
    r"(?i)(?:(?<![a-z0-9_])[a-z]:[\\/](?:users|桌面)[\\/]|/(?:home|users)/[^/\s]+)"
)


def relative_file(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise AssertionError(f"path must be artifact-relative: {value}")
    resolved = (ROOT / path).resolve()
    if ROOT.resolve() not in resolved.parents:
        raise AssertionError(f"path escapes artifact root: {value}")
    return resolved


def validate_paper_tasks() -> None:
    task_files = sorted((ROOT / "tasks").glob("*/*.yaml"))
    assert len(task_files) == 38, f"expected 38 paper tasks, found {len(task_files)}"
    for task_file in task_files:
        task = yaml.safe_load(task_file.read_text(encoding="utf-8")) or {}
        assert task.get("description"), f"missing description: {task_file}"
        assert task.get("api_contract"), f"missing public surface: {task_file}"
        reference = relative_file(str(task.get("reference_repository", "")))
        assert reference.is_dir(), f"missing reference: {reference.relative_to(ROOT)}"
        suites = task.get("test_suite") or {}
        assert set(suites) == SUITES, f"suite mismatch in {task_file.relative_to(ROOT)}: {set(suites)}"
        for suite_value in suites.values():
            suite_paths = suite_value if isinstance(suite_value, list) else [suite_value]
            for suite_path in suite_paths:
                assert relative_file(str(suite_path)).is_file(), f"missing suite: {suite_path}"
        baselines = task.get("baseline_metrics") or {}
        assert set(baselines) == SUITES, f"baseline mismatch in {task_file.relative_to(ROOT)}"


def validate_fresh() -> None:
    manifest = json.loads((ROOT / "fresh" / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((ROOT / "fresh" / "validation_report.json").read_text(encoding="utf-8"))
    reference_report = json.loads(
        (ROOT / "fresh" / "reference_validation_report.json").read_text(encoding="utf-8")
    )
    semantic_execution = json.loads(
        (ROOT / "fresh" / "semantic_execution_report.json").read_text(encoding="utf-8")
    )
    semantic_review = json.loads(
        (ROOT / "fresh" / "semantic_review_report.json").read_text(encoding="utf-8")
    )
    repos = manifest.get("repositories") or []
    assert manifest.get("construction_status") == "interface-validated"
    assert manifest.get("semantic_review_complete") is False
    assert manifest.get("task_count") == 50 == len(repos)
    assert report.get("checked") == report.get("passed") == 50
    assert report.get("failed") == 0
    assert reference_report.get("checked") == reference_report.get("passed") == 50
    assert reference_report.get("failed") == 0
    assert semantic_execution.get("checked") == semantic_execution.get("passed") == 50
    assert semantic_execution.get("failed") == 0
    assert semantic_review.get("checked") == semantic_review.get("passed") == 50
    assert semantic_review.get("failed") == 0
    cutoff = datetime.fromisoformat(manifest["cutoff"].replace("Z", "+00:00"))
    for repo in repos:
        created = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
        assert created >= cutoff, f"pre-cutoff repository: {repo['repository']}"
        assert re.fullmatch(r"[0-9a-f]{40}", repo["pinned_commit"])
        assert repo.get("eligible") is True

    task_files = sorted((ROOT / "fresh" / "tasks").glob("*/*.yaml"))
    assert len(task_files) == 50, f"expected 50 Fresh tasks, found {len(task_files)}"
    for task_file in task_files:
        task = yaml.safe_load(task_file.read_text(encoding="utf-8")) or {}
        assert task.get("description") and task.get("api_contract")
        assert set(task.get("test_suite") or {}) == SUITES
        assert set(task.get("baseline_metrics") or {}) == SUITES


def validate_anonymity() -> None:
    roots = [ROOT / name for name in ("evaluation", "tasks", "tests", "scripts", "fresh", "artifacts")]
    roots.append(ROOT / "README.md")
    offenders: list[str] = []
    for root in roots:
        files = [root] if root.is_file() else list(root.rglob("*"))
        for path in files:
            if not path.is_file() or path.suffix.lower() not in {".py", ".yaml", ".yml", ".md", ".txt", ".json"}:
                continue
            if "cache" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if LOCAL_PATH.search(text):
                offenders.append(path.relative_to(ROOT).as_posix())
    assert not offenders, "local absolute paths found in: " + ", ".join(offenders)


def main() -> None:
    validate_paper_tasks()
    validate_fresh()
    validate_anonymity()
    print("Artifact validation passed: 38 paper tasks; Fresh-50 50/50; no local identity paths")


if __name__ == "__main__":
    main()
