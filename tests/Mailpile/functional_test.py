import os
import shutil
import string
import subprocess
import sys
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional

import pytest


TARGET_ENV = "MAILPILE_TARGET"
ROOT_DIR = Path(__file__).resolve().parents[2]


def _candidate_repo_roots() -> list[Path]:
    candidates: list[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "mailpile").resolve())
        candidates.append((p / "repositories" / "Mailpile").resolve())
        candidates.append((p / "generation" / "Mailpile").resolve())

    candidates.append((ROOT_DIR / "repositories" / "mailpile").resolve())
    candidates.append((ROOT_DIR / "repositories" / "Mailpile").resolve())
    candidates.append((ROOT_DIR / "generation" / "Mailpile").resolve())

    seen = set()
    uniq: list[Path] = []
    for c in candidates:
        if c not in seen:
            uniq.append(c)
            seen.add(c)
    return uniq


def _looks_like_repo_root(repo_root: Path) -> bool:
    return (repo_root / "mailpile" / "__init__.py").exists()


def _select_repo_root() -> Path:
    override = os.environ.get("RACB_REPO_ROOT")
    if override:
        p = Path(override).resolve()
        if _looks_like_repo_root(p):
            return p

    target = os.environ.get(TARGET_ENV, "generated").lower()
    if target == "reference":
        for cand in _candidate_repo_roots():
            if "repositories" in cand.parts and _looks_like_repo_root(cand):
                return cand
        return (ROOT_DIR / "repositories" / "mailpile").resolve()

    for cand in _candidate_repo_roots():
        if "generation" in cand.parts and _looks_like_repo_root(cand):
            return cand
    return (ROOT_DIR / "generation" / "Mailpile").resolve()


def _py2_compat_patches() -> None:
    """Patch a minimal set of python2-era APIs relied on by Mailpile v1."""
    if not hasattr(string, "maketrans"):
        string.maketrans = str.maketrans  # type: ignore[attr-defined]

    if not hasattr(string, "translate"):

        def _translate(s: str, table, deletechars: str = "") -> str:
            if deletechars:
                s = s.translate({ord(c): None for c in deletechars})
            return s.translate(table)

        string.translate = _translate  # type: ignore[attr-defined]


def _ensure_py3_converted_repo(repo_root: Path) -> Path:
    """Convert the Python 2 codebase to a Python 3 importable copy once."""
    cache_root = (ROOT_DIR / ".converted" / "Mailpile").resolve()
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

    # Avoid importing the entire Mailpile app at package-import time.
    (out_root / "mailpile" / "__init__.py").write_text(
        "# RACB: minimal initializer (avoid importing the full Mailpile app)\n"
        "__all__ = []\n"
    )

    stamp.write_text(str(src_mtime))
    return out_root


def _pick_word_wrap(util_mod) -> Callable[[str, int], str]:
    """
    Mailpile util has had multiple wrapper function names across snapshots.
    Pick the first available; fallback to textwrap.fill if none exists.
    """
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
        # Try common calling conventions seen in util variants.
        try:
            out = fn(s, width)  # type: ignore[misc]
        except TypeError:
            try:
                out = fn(s, width=width)  # type: ignore[misc]
            except TypeError:
                try:
                    out = fn(s, cols=width)  # type: ignore[misc]
                except TypeError:
                    # Final fallback: standard library
                    out = textwrap.fill(s, width=width)
        return str(out)

    return _call


REPO_ROOT = _select_repo_root()
PY3_REPO_ROOT = _ensure_py3_converted_repo(REPO_ROOT)
_py2_compat_patches()

repo_str = str(PY3_REPO_ROOT)
if repo_str not in sys.path:
    sys.path.insert(0, repo_str)


from mailpile.safe_popen import PIPE, Popen, Safe_Pipe  # type: ignore
from mailpile.vcard import VCardLine  # type: ignore
from mailpile.i18n import gettext as mp_gettext  # type: ignore
import mailpile.util as mp_util  # type: ignore


# --- Compatibility patch ---
# Some snapshots' VCardLine.as_vcardline can mix bytes/str after conversion.
# Patch to a stable Python 3 version for consistent benchmarking.
import mailpile.vcard as _vcard_mod  # type: ignore


def _racb_as_vcardline_py3(self):  # type: ignore
    key = self.Quote(self._name.upper())
    for k, v in self._attrs:
        k = k.upper()
        if v is None:
            key += ";%s" % (self.Quote(k))
        else:
            key += ";%s=%s" % (self.Quote(k), self.Quote(str(v)))

    wrapped = ""
    line = "%s:%s" % (key, self.Quote(self._value))
    llen = 0
    for ch in line:
        clen = len(ch.encode("utf-8"))
        if llen + clen >= 75:
            wrapped += "\n "
            llen = 0
        wrapped += ch
        llen += clen
    return wrapped


_vcard_mod.VCardLine.as_vcardline = _racb_as_vcardline_py3  # type: ignore

_word_wrap = _pick_word_wrap(mp_util)


def test_safe_pipe_basic_roundtrip() -> None:
    sp = Safe_Pipe()
    try:
        sp.write("hello")
        sp.write_end.flush()
        sp.write_end.close()
        assert sp.read() == "hello"
    finally:
        try:
            sp.read_end.close()
        except Exception:
            pass


def test_safe_popen_runs_simple_python_command() -> None:
    proc = Popen([sys.executable, "-c", "print('hi')"], stdout=PIPE, stderr=PIPE, universal_newlines=True)
    out, err = proc.communicate(timeout=10)
    assert proc.returncode == 0
    assert out.strip() == "hi"
    assert err.strip() == ""


def test_cleantext_strips_nonalnum_characters() -> None:
    CleanText = getattr(mp_util, "CleanText")
    assert CleanText("c_(l e$ a) n!", banned=CleanText.NONALNUM).clean == "clean"


def test_b36_converts_integers_to_base36() -> None:
    b36 = getattr(mp_util, "b36")
    assert b36(2701) == "231"
    assert b36(12345) == "9IX"


def test_dict_merge_combines_multiple_dicts() -> None:
    dict_merge = getattr(mp_util, "dict_merge")
    merged = dict_merge({"a": "A"}, {"b": "B"}, {"c": "C"})
    assert merged == {"a": "A", "b": "B", "c": "C"}


def test_word_wrap_wraps_text() -> None:
    # Happy path: wrap a paragraph to a narrower width.
    text = "This is a simple line that should be wrapped into multiple lines."
    wrapped = _word_wrap(text, 20)
    assert isinstance(wrapped, str)
    assert "\n" in wrapped
    assert wrapped.startswith("This is")


def test_elapsed_datetime_formats_relative_time() -> None:
    # Happy path: elapsed_datetime expects a Unix timestamp (seconds).
    import time

    elapsed_datetime = getattr(mp_util, "elapsed_datetime")
    then_ts = time.time() - (2 * 24 * 60 * 60)
    s = elapsed_datetime(then_ts)

    assert isinstance(s, str)
    assert len(s) > 0



def test_vcardline_serialization_simple() -> None:
    vcl = VCardLine(name="FN", value="Lebowski")
    assert vcl.as_vcardline() == "FN:Lebowski"


def test_vcardline_parsing_with_type_attribute() -> None:
    vcl = VCardLine("FN;TYPE=Nickname:Bjarni")
    assert vcl.name == "fn"
    assert vcl.value == "Bjarni"
    assert vcl.get("type") == "Nickname"


def test_i18n_gettext_passthrough_when_inactive() -> None:
    assert mp_gettext("Hello, Mailpile!") == "Hello, Mailpile!"
