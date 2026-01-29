import argparse
import hashlib
import json
import re
from pathlib import Path

import pandas as pd
import yaml


def safe_read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def classify_failure(stdout: str, functional: dict):
    """
    Returns (failure_stage, failure_type)
      failure_stage ∈ {pass, pre-test, in-test}
      failure_type  ∈ {none, import_error, syntax_error, collection_error, pytest_internal_error,
                       timeout, assertion_failure, runtime_exception, test_failure, test_error,
                       unknown_failure}
    """
    s = stdout or ""
    lower = s.lower()

    # Pass heuristic
    if functional.get("returncode", None) == 0 and functional.get("failed", 0) == 0 and "error" not in lower:
        return ("pass", "none")

    # Pre-test: pytest collection / import stage
    if ("error collecting" in lower) or ("error during collection" in lower) or ("while importing test module" in lower):
        if ("modulenotfounderror" in lower) or ("importerror" in lower) or ("cannot import name" in lower):
            return ("pre-test", "import_error")
        if ("syntaxerror" in lower) or ("indentationerror" in lower) or ("taberror" in lower):
            return ("pre-test", "syntax_error")
        return ("pre-test", "collection_error")

    if "internalerror>" in lower:
        return ("pre-test", "pytest_internal_error")

    if (("syntaxerror" in lower) or ("indentationerror" in lower) or ("taberror" in lower)) and functional.get("passed", 0) == 0:
        return ("pre-test", "syntax_error")

    # Timeout
    if ("timeout" in lower) or ("timed out" in lower):
        # if any hint tests ran, treat as in-test timeout
        if functional.get("passed", 0) > 0 or functional.get("failed", 0) > 0 or "collected" in lower:
            return ("in-test", "timeout")
        return ("pre-test", "timeout")

    # In-test FAILURES
    if ("==== failures" in lower) or ("\nFAILURES\n" in s) or ("== FAILURES" in s):
        if "assertionerror" in lower:
            return ("in-test", "assertion_failure")
        if re.search(r"\nE\s+[A-Za-z_]\w*(?:Error|Exception)\b", s):
            return ("in-test", "runtime_exception")
        return ("in-test", "test_failure")

    # In-test ERRORS (not collection)
    if ("==== errors" in lower) and ("error collecting" not in lower):
        return ("in-test", "test_error")

    if functional.get("failed", 0) > 0:
        return ("in-test", "test_failure")

    return ("pre-test", "unknown_failure")


def extract_primary_block(stdout: str, stage: str, max_len: int = 4000):
    """
    Extract a compact excerpt for quick inspection.
    """
    if not stdout:
        return ""
    s = stdout.replace("\r\n", "\n").replace("\r", "\n")
    scan = s[:200000]

    if stage == "pre-test":
        if "ERROR collecting" in scan:
            idx = scan.find("ERROR collecting")
            hdr = scan.rfind("====", 0, idx)
            start = hdr if hdr != -1 else idx
            return scan[start:start + max_len]
        if "==== ERRORS" in scan:
            idx = scan.find("==== ERRORS")
            return scan[idx:idx + max_len]
        tb = scan.find("Traceback")
        if tb != -1:
            return scan[tb:tb + max_len]
        return scan[:max_len]

    if stage == "in-test":
        if "==== FAILURES" in scan:
            idx = scan.find("==== FAILURES")
            seg = scan[idx:idx + 60000]
            lines = seg.splitlines()

            # first failure block separated by ______
            start_i = None
            for i, ln in enumerate(lines):
                if len(ln) >= 10 and set(ln.strip()) == {"_"}:
                    start_i = i
                    break

            if start_i is not None:
                end_i = None
                for j in range(start_i + 1, len(lines)):
                    ln = lines[j]
                    if len(ln) >= 10 and set(ln.strip()) == {"_"}:
                        end_i = j
                        break
                if end_i is None:
                    end_i = min(len(lines), start_i + 120)
                return "\n".join(lines[start_i:end_i])[:max_len]

            return seg[:max_len]

        if "==== ERRORS" in scan:
            idx = scan.find("==== ERRORS")
            return scan[idx:idx + max_len]

        return scan[:max_len]

    return scan[:max_len]


def extract_exception_line(block: str):
    """
    Parse pytest 'E   XxxError: msg' line (if any).
    """
    if not block:
        return ("", "")
    ex_type, ex_msg = "", ""
    for ln in block.splitlines():
        if ln.startswith("E   ") or ln.startswith("E  "):
            content = ln.lstrip("E ").strip()
            ex_msg = content
            m = re.match(r"([A-Za-z_]\w*(?:Error|Exception))\s*:\s*(.*)", content)
            if m:
                ex_type, ex_msg = m.group(1), m.group(2)
    return ex_type, ex_msg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ex2_root", required=True, help="Extracted Ex2 root folder (contains model subfolders)")
    ap.add_argument("--out_dir", default="rq2_out", help="Output folder")
    args = ap.parse_args()

    ex2_root = Path(args.ex2_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_records = []
    failure_records = []

    model_dirs = sorted([p for p in ex2_root.iterdir() if p.is_dir()])

    for model_dir in model_dirs:
        model = model_dir.name
        res_dir = model_dir / "results"
        if not res_dir.exists():
            continue

        for ypath in res_dir.glob("*_results.yaml"):
            project = ypath.name.replace("_results.yaml", "")
            y = yaml.safe_load(safe_read_text(ypath)) or {}

            functional = (y.get("results", {}) or {}).get("functional", {}) or {}
            stdout = functional.get("stdout", "") or ""

            # fallback to pytest log
            if not stdout:
                log_path = model_dir / "results" / project / "pytest_logs" / "functional.log"
                if log_path.exists():
                    stdout = safe_read_text(log_path)

            stage, ftype = classify_failure(stdout, functional)
            excerpt = extract_primary_block(stdout, stage if stage != "pass" else "in-test")
            ex_type, ex_msg = extract_exception_line(excerpt)

            rel_log = Path(model, "results", project, "pytest_logs", "functional.log")
            pytest_log_path = str(rel_log) if (ex2_root / rel_log).exists() else ""

            base = {
                "model": model,
                "project": project,
                "failure_stage": stage,
                "failure_type": ftype,
                "exception_type": ex_type,
                "exception_msg": ex_msg,
                "returncode": functional.get("returncode"),
                "elapsed_time_s": functional.get("elapsed_time_s"),
                "avg_memory_mb": functional.get("avg_memory_mb"),
                "avg_cpu_percent": functional.get("avg_cpu_percent"),
                "passed": functional.get("passed"),
                "failed": functional.get("failed"),
                "skipped": functional.get("skipped"),
                "total": functional.get("total"),
                "functional_score": y.get("functional_score"),
                "non_functional_score": y.get("non_functional_score"),
                "timestamp": y.get("timestamp"),
                "pytest_log_path": pytest_log_path,
                "stdout_excerpt": excerpt if excerpt else (stdout[:4000] if stdout else ""),
                "stdout_sha1": hashlib.sha1(stdout.encode("utf-8", errors="replace")).hexdigest() if stdout else "",
                "stdout_len": len(stdout) if stdout else 0,
            }

            all_records.append(base)

            if stage != "pass":
                fail = dict(base)
                fail["stdout"] = stdout  # full output in jsonl
                failure_records.append(fail)

    df_all = pd.DataFrame(all_records)
    df_fail = pd.DataFrame(failure_records)

    out_jsonl = out_dir / "RQ2_failure_cases.jsonl"
    out_fail_csv = out_dir / "RQ2_failure_cases.csv"
    out_all_csv = out_dir / "RQ2_all_cases.csv"

    with out_jsonl.open("w", encoding="utf-8") as f:
        for rec in failure_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # CSV: drop huge stdout
    if "stdout" in df_fail.columns:
        df_fail.drop(columns=["stdout"]).to_csv(out_fail_csv, index=False)
    else:
        df_fail.to_csv(out_fail_csv, index=False)

    df_all.to_csv(out_all_csv, index=False)

    print("Saved:")
    print(" -", out_jsonl)
    print(" -", out_fail_csv)
    print(" -", out_all_csv)
    print(f"All pairs: {len(df_all)}, Failures: {len(df_fail)}")


if __name__ == "__main__":
    main()
