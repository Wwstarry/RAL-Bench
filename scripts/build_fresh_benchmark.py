"""Freeze and validate the 50-repository Fresh-50 source manifest.

This script verifies provenance before task authors write requirements, public
surfaces, and RAL-specific black-box tests. It deliberately does not treat an
upstream test suite as a RAL-Bench oracle.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable

ROOT = Path(__file__).resolve().parents[1]
FRESH = ROOT / "fresh"
CANDIDATES = FRESH / "candidates.txt"
CACHE = FRESH / "cache"
MANIFEST = FRESH / "manifest.json"
REPORT = FRESH / "validation_report.json"
CUTOFF = datetime(2026, 9, 1, tzinfo=timezone.utc)

SEARCHES = (
    "created:>=2026-09-01 language:Python archived:false fork:false size:10..20000",
    "created:>=2026-09-01 language:Python topic:cli archived:false fork:false size:5..20000",
    "created:>=2026-09-01 language:Python topic:library archived:false fork:false size:5..20000",
    "created:>=2026-09-01 language:Python topic:python-library archived:false fork:false size:5..20000",
)


def candidates() -> list[str]:
    repos = [line.strip() for line in CANDIDATES.read_text(encoding="utf-8").splitlines()]
    repos = [repo for repo in repos if repo and not repo.startswith("#")]
    if len(repos) != 50 or len(set(map(str.lower, repos))) != 50:
        raise ValueError("fresh/candidates.txt must contain exactly 50 unique repositories")
    return repos


def github_json(url: str) -> Dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "RAL-Bench-Fresh-Builder",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def discover() -> Dict[str, Dict[str, Any]]:
    found: Dict[str, Dict[str, Any]] = {}
    for query in SEARCHES:
        params = urllib.parse.urlencode(
            {"q": query, "sort": "stars", "order": "desc", "per_page": 100}
        )
        payload = github_json(f"https://api.github.com/search/repositories?{params}")
        for item in payload.get("items", []):
            found[item["full_name"].lower()] = item
    return found


def run(command: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300,
    )
    if result.returncode:
        raise RuntimeError(result.stdout.strip() or f"exit {result.returncode}")
    return result.stdout.strip()


def pinned_sha(item: Dict[str, Any]) -> str:
    output = run(["git", "ls-remote", item["clone_url"], f"refs/heads/{item['default_branch']}"])
    sha = output.split()[0] if output else ""
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise RuntimeError("default branch did not resolve to a 40-character commit SHA")
    return sha


def clone_and_inspect(item: Dict[str, Any], sha: str) -> Dict[str, Any]:
    task_id = re.sub(r"[^a-z0-9]+", "-", item["full_name"].lower()).strip("-")
    checkout = CACHE / task_id
    if not (checkout / ".git").is_dir():
        checkout.parent.mkdir(parents=True, exist_ok=True)
        run(
            [
                "git",
                "clone",
                "--quiet",
                "--depth",
                "1",
                "--filter=blob:none",
                "--branch",
                item["default_branch"],
                item["clone_url"],
                str(checkout),
            ]
        )
    current = run(["git", "rev-parse", "HEAD"], cwd=checkout)
    if current != sha:
        run(["git", "fetch", "--quiet", "--depth", "1", "origin", sha], cwd=checkout)
        run(["git", "checkout", "--quiet", "--detach", sha], cwd=checkout)

    files = [path for path in checkout.rglob("*") if path.is_file() and ".git" not in path.parts]
    readmes = [path for path in files if path.name.lower().startswith("readme")]
    python_files = [path for path in files if path.suffix == ".py"]
    packaging_names = {"pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"}
    packaging = [path for path in files if path.name in packaging_names]
    upstream_tests = [
        path
        for path in python_files
        if "test" in path.name.lower() or any(part.lower() in {"test", "tests"} for part in path.parts)
    ]
    checks = {
        "readme": bool(readmes),
        "python_source": bool(python_files),
        "packaging": bool(packaging),
        "upstream_tests_present": bool(upstream_tests),
        "pinned_checkout": current == sha,
    }
    return {
        "checks": checks,
        "python_files": len(python_files),
        "upstream_test_files": len(upstream_tests),
        "eligible": all(checks.values()),
    }


def iso_date(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_one(repo: str, discovered: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    item = discovered.get(repo.lower())
    if item is None:
        return {"repository": repo, "eligible": False, "error": "not returned by frozen search queries"}
    created = iso_date(item["created_at"])
    sha = pinned_sha(item)
    inspected = clone_and_inspect(item, sha)
    license_info = item.get("license") or {}
    return {
        "task_id": re.sub(r"[^a-z0-9]+", "-", repo.lower()).strip("-"),
        "repository": item["full_name"],
        "source_url": item["html_url"],
        "created_at": item["created_at"],
        "created_after_cutoff": created >= CUTOFF,
        "pinned_commit": sha,
        "default_branch": item["default_branch"],
        "license": license_info.get("spdx_id"),
        "description": item.get("description") or "",
        "stars_at_freeze": item.get("stargazers_count", 0),
        **inspected,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    selected = candidates()
    discovered = discover()
    records: list[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        jobs = {executor.submit(validate_one, repo, discovered): repo for repo in selected}
        for job in as_completed(jobs):
            repo = jobs[job]
            try:
                records.append(job.result())
            except Exception as exc:  # retain a complete audit report
                records.append({"repository": repo, "eligible": False, "error": str(exc)})
            print(f"[{len(records):02d}/50] {repo}")

    order = {repo.lower(): index for index, repo in enumerate(selected)}
    records.sort(key=lambda row: order[row["repository"].lower()])
    passed = [row for row in records if row.get("eligible") and row.get("created_after_cutoff")]
    freeze = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    manifest = {
        "benchmark": "RAL-Bench Fresh-50",
        "version": "2026.10",
        "cutoff": "2026-09-01T00:00:00Z",
        "frozen_at": freeze,
        "task_count": len(passed),
        "construction_status": "source-validated",
        "repositories": passed,
    }
    report = {
        "benchmark": "RAL-Bench Fresh-50",
        "cutoff": "2026-09-01T00:00:00Z",
        "checked": len(records),
        "passed": len(passed),
        "failed": len(records) - len(passed),
        "all_created_after_cutoff": all(row.get("created_after_cutoff") for row in passed),
        "records": records,
    }
    write_json(MANIFEST, manifest)
    write_json(REPORT, report)
    print(f"Fresh source validation: {len(passed)}/50 passed")
    return 0 if len(passed) == 50 else 1


if __name__ == "__main__":
    raise SystemExit(main())
