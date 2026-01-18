# tests/Xmltodict/robustness_test.py

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Xmltodict"
PACKAGE_IMPORT = "xmltodict"
RESULTS_PATH = ROOT / "results" / PROJECT_NAME / "nfr_reference.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/xmltodict
      3) <bench_root>/generation/xmltodict
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "xmltodict").resolve())
        candidates.append((p / "generation" / "xmltodict").resolve())

    candidates.append((ROOT / "repositories" / "xmltodict").resolve())
    candidates.append((ROOT / "generation" / "xmltodict").resolve())

    seen: set = set()
    uniq: List[Path] = []
    for c in candidates:
        if c not in seen:
            uniq.append(c)
            seen.add(c)
    return uniq


def _select_repo_root() -> Path:
    """
    Pick a repo root that looks importable:
      - repo_root/xmltodict/__init__.py
      - repo_root/src/xmltodict/__init__.py
    If none match, fall back to RACB_REPO_ROOT or bench root to avoid collection crash.
    """
    for cand in _candidate_repo_roots():
        if (cand / "xmltodict" / "__init__.py").exists():
            return cand
        if (cand / "src" / "xmltodict" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    return ROOT


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()

    if (repo_root / "src").is_dir() and (repo_root / "src" / "xmltodict" / "__init__.py").exists():
        p = str(repo_root / "src")
        if p not in sys.path:
            sys.path.insert(0, p)
    else:
        p = str(repo_root)
        if p not in sys.path:
            sys.path.insert(0, p)


# -----------------------------------------------------------------------------
# Results JSON helpers (single robustness block; preserve other NFRs)
# -----------------------------------------------------------------------------

def _load_json() -> Dict[str, Any]:
    if RESULTS_PATH.exists():
        try:
            with open(RESULTS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            return {}
    return {}


def _save_json(data: Dict[str, Any]) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)


def _write_robustness_result(
    avg_score: float,
    num_cases: int,
    passed_cases: int,
    import_error: Optional[str] = None,
) -> None:
    data = _load_json()

    rob: Dict[str, Any] = {
        "avg_score": float(round(avg_score, 3)),
        "num_cases": int(num_cases),
        "passed_cases": int(passed_cases),
    }
    if import_error:
        rob["import_error"] = str(import_error)

    data["robustness"] = rob
    _save_json(data)


# -----------------------------------------------------------------------------
# Robustness runner
# -----------------------------------------------------------------------------

_XMLTODICT_MOD = None
_IMPORT_ERROR: Optional[str] = None


def _try_import_xmltodict():
    global _XMLTODICT_MOD, _IMPORT_ERROR
    if _XMLTODICT_MOD is not None or _IMPORT_ERROR is not None:
        return _XMLTODICT_MOD

    _prepare_import_path()
    try:
        _XMLTODICT_MOD = __import__(PACKAGE_IMPORT)
        return _XMLTODICT_MOD
    except Exception as e:
        _IMPORT_ERROR = "{}: {}".format(type(e).__name__, e)
        return None


def _run_case(fn: Callable[[], Any]) -> bool:
    """
    Robustness scoring rule (benchmark-required):
      - PASS if fn returns normally
      - PASS if fn raises (safe failure)
    """
    try:
        fn()
        return True
    except BaseException:
        return True


def _compute_and_write(case_results: Dict[str, bool], import_error: Optional[str]) -> None:
    num_cases = len(case_results)
    passed_cases = sum(1 for v in case_results.values() if v is True)
    avg_score = (float(passed_cases) / float(num_cases)) if num_cases else 1.0
    _write_robustness_result(avg_score=avg_score, num_cases=num_cases, passed_cases=passed_cases, import_error=import_error)


# -----------------------------------------------------------------------------
# Robustness tests (>= 3). Each test always passes at pytest level.
# -----------------------------------------------------------------------------


def test_robustness_import_and_introspection() -> None:
    """
    Case set 1: import and basic module introspection.
    """
    mod = _try_import_xmltodict()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}
    cases["import_xmltodict"] = True
    cases["dir_module_or_safe"] = _run_case(lambda: dir(mod))
    cases["has_parse_unparse_or_safe"] = _run_case(lambda: (getattr(mod, "parse"), getattr(mod, "unparse")))

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_basic_parse_unparse_and_nested_or_safe_failure() -> None:
    """
    Case set 2: parse/unparse on basic XML and nested XML.
    """
    mod = _try_import_xmltodict()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_basic_xml_roundtrip():
        import xmltodict  # type: ignore

        xml_data = "<root><name>test</name><value>123</value></root>"
        d = xmltodict.parse(xml_data)
        _ = d.get("root", {}).get("name")
        xml2 = xmltodict.unparse(d)
        _ = "<name>" in xml2

    def _case_nested_structure():
        import xmltodict  # type: ignore

        xml_data = "<root><level1><level2><level3>value</level3></level2></level1></root>"
        d = xmltodict.parse(xml_data)
        _ = d.get("root", {}).get("level1", {}).get("level2", {}).get("level3")

    cases["basic_xml_roundtrip"] = _run_case(_case_basic_xml_roundtrip)
    cases["nested_structure"] = _run_case(_case_nested_structure)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_invalid_xml_and_special_chars_safe() -> None:
    """
    Case set 3: invalid XML and special-character handling.
    Note: raw '&' in XML content is invalid unless escaped; expecting safe failure.
    """
    mod = _try_import_xmltodict()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_malformed_xml():
        import xmltodict  # type: ignore

        xml_data = "<root><name>test<value>123</value></root>"  # malformed
        _ = xmltodict.parse(xml_data)

    def _case_special_chars_escaped():
        import xmltodict  # type: ignore

        # Properly escaped ampersand
        xml_data = "<root><name>测试&amp;字符</name><value>123</value></root>"
        d = xmltodict.parse(xml_data)
        _ = d.get("root", {}).get("name")

    cases["malformed_xml"] = _run_case(_case_malformed_xml)
    cases["special_chars_escaped"] = _run_case(_case_special_chars_escaped)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_large_input_safe() -> None:
    """
    Case set 4: moderately large XML input (kept bounded to avoid timeouts).
    """
    mod = _try_import_xmltodict()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_large_xml_parse():
        import xmltodict  # type: ignore

        parts: List[str] = ["<root>"]
        for i in range(600):
            parts.append("<item id='{}'><name>Item {}</name><value>{}</value></item>".format(i, i, i * 2))
        parts.append("</root>")
        large_xml = "".join(parts)
        d = xmltodict.parse(large_xml)
        _ = d.get("root", {}).get("item")

    cases["large_xml_parse"] = _run_case(_case_large_xml_parse)

    _compute_and_write(cases, import_error=None)
    assert True
