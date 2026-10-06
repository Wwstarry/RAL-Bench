import argparse
import hashlib
import json
import re
from pathlib import Path

import pandas as pd
import yaml


def safe_read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# --------- 原始 failure_type（细粒度）识别：与之前一致 ----------
def classify_failure(stdout: str, functional: dict):
    s = stdout or ""
    lower = s.lower()

    if functional.get("returncode", None) == 0 and functional.get("failed", 0) == 0 and "error" not in lower:
        return ("pass", "none")

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

    if ("timeout" in lower) or ("timed out" in lower):
        if functional.get("passed", 0) > 0 or functional.get("failed", 0) > 0 or "collected" in lower:
            return ("in-test", "timeout")
        return ("pre-test", "timeout")

    if ("==== failures" in lower) or ("\nFAILURES\n" in s) or ("== FAILURES" in s):
        if "assertionerror" in lower:
            return ("in-test", "assertion_failure")
        if re.search(r"\nE\s+[A-Za-z_]\w*(?:Error|Exception)\b", s):
            return ("in-test", "runtime_exception")
        return ("in-test", "test_failure")

    if ("==== errors" in lower) and ("error collecting" not in lower):
        return ("in-test", "test_error")

    if functional.get("failed", 0) > 0:
        return ("in-test", "test_failure")

    return ("pre-test", "unknown_failure")


def extract_primary_block(stdout: str, stage: str, max_len: int = 4000):
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
            return seg[:max_len]
        if "==== ERRORS" in scan:
            idx = scan.find("==== ERRORS")
            return scan[idx:idx + max_len]
        return scan[:max_len]

    return scan[:max_len]


def extract_exception_line(block: str):
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


# --------- 3 类 taxonomy（含对 unknown 的二阶段归因） ----------
GROUP3 = {
    "import_error": "Executability & Environment",
    "syntax_error": "Executability & Environment",
    "collection_error": "Executability & Environment",

    "assertion_failure": "Functional Correctness",
    "test_failure": "Functional Correctness",  # 默认；如识别到异常再改到 Runtime

    "runtime_exception": "Runtime Robustness & Efficiency",
    "timeout": "Runtime Robustness & Efficiency",
    "test_error": "Runtime Robustness & Efficiency",
    "pytest_internal_error": "Runtime Robustness & Efficiency",

    "unknown_failure": "Non-diagnostic (Evidence-Insufficient)",  # 临时
}

def merged_text(row):
    return " ".join([
        str(row.get("stdout_excerpt", "")),
        str(row.get("exception_type", "")),
        str(row.get("exception_msg", "")),
    ]).lower()

def refine_to_group3(row):
    ft = row["failure_type"]
    g = GROUP3.get(ft, "Non-diagnostic (Evidence-Insufficient)")
    text = merged_text(row)

    # 1) 把 test_failure 中明显的异常线索划到 Runtime
    if ft == "test_failure":
        if re.search(r"\b(typeerror|valueerror|keyerror|indexerror|attributeerror|filenotfounderror|oserror)\b", text):
            return "Runtime Robustness & Efficiency"
        if "timeout" in text or "timed out" in text:
            return "Runtime Robustness & Efficiency"

    # 2) 对 unknown_failure 做再归因：尽量并入 3 类之一
    if ft == "unknown_failure":
        if any(k in text for k in ["modulenotfounderror", "importerror", "no module named", "cannot import name"]):
            return "Executability & Environment"
        if any(k in text for k in ["syntaxerror", "indentationerror", "taberror"]):
            return "Executability & Environment"
        if any(k in text for k in ["timeout", "timed out", "hang", "hung"]):
            return "Runtime Robustness & Efficiency"
        if re.search(r"\b([a-z_]\w*(error|exception))\b", text):
            return "Runtime Robustness & Efficiency"
        # 保留真正证据不足的 unknown：主图里我们会并入 Runtime（更保守）
        return "Non-diagnostic (Evidence-Insufficient)"

    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ex2_root", required=True, help="Ex2 extracted root folder (contains model subfolders)")
    ap.add_argument("--out_dir", default="rq2_out", help="Output folder")
    args = ap.parse_args()

    ex2_root = Path(args.ex2_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_records = []
    failure_records = []

    for model_dir in sorted([p for p in ex2_root.iterdir() if p.is_dir()]):
        model = model_dir.name
        res_dir = model_dir / "results"
        if not res_dir.exists():
            continue

        for ypath in res_dir.glob("*_results.yaml"):
            project = ypath.name.replace("_results.yaml", "")
            y = yaml.safe_load(safe_read_text(ypath)) or {}

            functional = (y.get("results", {}) or {}).get("functional", {}) or {}
            stdout = functional.get("stdout", "") or ""

            # fallback to pytest log if yaml missing stdout
            if not stdout:
                log_path = model_dir / "results" / project / "pytest_logs" / "functional.log"
                if log_path.exists():
                    stdout = safe_read_text(log_path)

            stage, ftype = classify_failure(stdout, functional)
            excerpt = extract_primary_block(stdout, stage if stage != "pass" else "in-test")
            ex_type, ex_msg = extract_exception_line(excerpt)

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
                "timestamp": y.get("timestamp"),
                "stdout_excerpt": excerpt if excerpt else (stdout[:4000] if stdout else ""),
                "stdout_sha1": hashlib.sha1(stdout.encode("utf-8", errors="replace")).hexdigest() if stdout else "",
                "stdout_len": len(stdout) if stdout else 0,
            }

            all_records.append(base)

            if stage != "pass":
                failure_records.append({**base, "stdout": stdout})

    df_all = pd.DataFrame(all_records)
    df_fail = pd.DataFrame(failure_records)

    # Add 3-class labels
    df_fail["failure_group3_raw"] = df_fail["failure_type"].map(GROUP3).fillna("Non-diagnostic (Evidence-Insufficient)")
    df_fail["failure_group3"] = df_fail.apply(refine_to_group3, axis=1)

    # For the main figure: merge remaining non-diagnostic into Runtime (conservative)
    df_fail["failure_group3_main"] = df_fail["failure_group3"].replace(
        {"Non-diagnostic (Evidence-Insufficient)": "Runtime Robustness & Efficiency"}
    )

    out_jsonl = out_dir / "RQ2_failure_cases.jsonl"
    out_fail_csv = out_dir / "RQ2_failure_cases.csv"
    out_fail_group3_csv = out_dir / "RQ2_failure_cases_group3.csv"
    out_all_csv = out_dir / "RQ2_all_cases.csv"

    # JSONL (failures only, with full stdout)
    with out_jsonl.open("w", encoding="utf-8") as f:
        for rec in failure_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # CSV (failures only, no full stdout)
    df_fail.drop(columns=["stdout"]).to_csv(out_fail_csv, index=False)
    df_fail.drop(columns=["stdout"]).to_csv(out_fail_group3_csv, index=False)  # same file but with group3 cols included
    df_all.to_csv(out_all_csv, index=False)

    print("Saved:")
    print(" -", out_jsonl)
    print(" -", out_fail_csv)
    print(" -", out_fail_group3_csv)
    print(" -", out_all_csv)
    print(f"All pairs: {len(df_all)}, Failures: {len(df_fail)}")


if __name__ == "__main__":
    main()
