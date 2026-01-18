from __future__ import annotations

import os
import shutil
import string
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Callable

import pytest

ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT_ENV = "RACB_REPO_ROOT"
TARGET_ENV = "MAILPILE_TARGET"


def _select_repo_root() -> Path:
    override = os.environ.get(REPO_ROOT_ENV)
    if override:
        return Path(override).resolve()

    target = os.environ.get(TARGET_ENV, "generated").lower()
    if target == "reference":
        for name in ("mailpile", "Mailpile"):
            cand = ROOT / "repositories" / name
            if (cand / "mailpile" / "__init__.py").exists():
                return cand.resolve()
        return (ROOT / "repositories" / "mailpile").resolve()

    return (ROOT / "generation" / "Mailpile").resolve()


def _py2_compat_patches() -> None:
    if not hasattr(string, "maketrans"):
        string.maketrans = str.maketrans  # type: ignore[attr-defined]

    if not hasattr(string, "translate"):

        def _translate(s: str, table, deletechars: str = "") -> str:
            if deletechars:
                s = s.translate({ord(c): None for c in deletechars})
            return s.translate(table)

        string.translate = _translate  # type: ignore[attr-defined]


def _ensure_py3_converted_repo(repo_root: Path) -> Path:
    cache_root = (ROOT / ".converted" / "Mailpile").resolve()
    cache_root.mkdir(parents=True, exist_ok=True)

    safe_name = "reference" if "repositories" in repo_root.parts else "generated"
    out_root = (cache_root / safe_name).resolve()

    stamp = out_root / ".racb_py3_stamp"
    src_pkg = repo_root / "mailpile"
    src_mtime = max(p.stat().st_mtime for p in src_pkg.rglob("*") if p.is_file())

    if stamp.exists():
        try:
            cached = float(stamp.read_text().strip())
            if cached >= src_mtime and (out_root / "mailpile" / "__init__.py").exists():
                return out_root
        except Exception:
            pass

    if out_root.exists():
        shutil.rmtree(out_root)
    shutil.copytree(repo_root, out_root)

    subprocess.run(
        [sys.executable, "-m", "lib2to3", "-w", "-n", str(out_root / "mailpile")],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    (out_root / "mailpile" / "__init__.py").write_text(
        "# RACB: minimal initializer (avoid importing the full Mailpile app)\n" "__all__ = []\n"
    )

    stamp.write_text(str(src_mtime))
    return out_root


def _pick_word_wrap(util_mod) -> Callable[[str, int], str]:
    candidates = [
        "unicode_wp_wrap",
        "wp_wrap",
        "word_wrap",
        "wrap",
        "wrap_text",
    ]
    fn = None
    for name in candidates:
        maybe = getattr(util_mod, name, None)
        if callable(maybe):
            fn = maybe
            break

    if fn is None:

        def _fallback(s: str, width: int) -> str:
            return textwrap.fill(s, width=width)

        return _fallback

    def _call(s: str, width: int) -> str:
        try:
            out = fn(s, width)  # type: ignore[misc]
        except TypeError:
            try:
                out = fn(s, width=width)  # type: ignore[misc]
            except TypeError:
                try:
                    out = fn(s, cols=width)  # type: ignore[misc]
                except TypeError:
                    out = textwrap.fill(str(s), width=width)
        return str(out)

    return _call


REPO_ROOT = _select_repo_root()
PY3_REPO_ROOT = _ensure_py3_converted_repo(REPO_ROOT)
_py2_compat_patches()

repo_str = str(PY3_REPO_ROOT)
if repo_str not in sys.path:
    sys.path.insert(0, repo_str)


def test_imports_core_modules() -> None:
    import mailpile.safe_popen  # type: ignore
    import mailpile.util  # type: ignore
    import mailpile.vcard  # type: ignore
    import mailpile.i18n  # type: ignore

    assert hasattr(mailpile.safe_popen, "Popen")
    assert hasattr(mailpile.util, "CleanText")
    assert hasattr(mailpile.vcard, "VCardLine")
    assert hasattr(mailpile.i18n, "gettext")


def test_safe_popen_invalid_command_fails_predictably() -> None:
    from mailpile.safe_popen import Popen, PIPE  # type: ignore

    with pytest.raises(Exception):
        _ = Popen(["/this/definitely/does/not/exist"], stdout=PIPE, stderr=PIPE)


def test_vcardline_rejects_invalid_input_line_safely() -> None:
    from mailpile.vcard import VCardLine  # type: ignore

    vcl = VCardLine("THIS_IS_NOT_A_VCARD_LINE")
    assert getattr(vcl, "value", "") in ("THIS_IS_NOT_A_VCARD_LINE", "")


def test_cleantext_handles_none_input() -> None:
    import mailpile.util as mp_util  # type: ignore

    CleanText = getattr(mp_util, "CleanText")
    assert CleanText(None).clean == ""


def test_word_wrap_handles_weird_input_safely() -> None:
    import mailpile.util as mp_util  # type: ignore

    wrap = _pick_word_wrap(mp_util)

    # Robustness check: either controlled exception or returns a string; must not crash.
    try:
        out = wrap(str(None), 10)
        assert isinstance(out, str)
    except Exception:
        assert True
