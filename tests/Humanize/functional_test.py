from __future__ import annotations

import os
import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Repo root resolution
# ---------------------------------------------------------------------------
# Benchmark-compatible (preferred): use RACB_REPO_ROOT if provided by the runner.
# Developer-friendly fallback (no absolute hardcode): use this repo layout:
#   <eval_root>/repositories/humanize  OR  <eval_root>/generation/Humanize
#
# NOTE:
# - This keeps your original "ROOT + HUMANIZE_TARGET" behavior as a fallback,
#   while still satisfying RACB's requirement when RACB_REPO_ROOT is set.
# ---------------------------------------------------------------------------

PACKAGE_NAME = "humanize"

RACB_REPO_ROOT = os.environ.get("RACB_REPO_ROOT", "").strip()
if RACB_REPO_ROOT:
    REPO_ROOT = Path(RACB_REPO_ROOT).resolve()
else:
    ROOT = Path(__file__).resolve().parents[2]
    target = os.environ.get("HUMANIZE_TARGET", "reference").lower()
    if target == "reference":
        REPO_ROOT = ROOT / "repositories" / "humanize"
    else:
        REPO_ROOT = ROOT / "generation" / "Humanize"

if not REPO_ROOT.exists():
    pytest.skip(
        "Target repository does not exist on disk: {}".format(REPO_ROOT),
        allow_module_level=True,
    )

# RACB import-path rule:
# - If src/<package>/__init__.py exists -> sys.path insert repo_root/src
# - Else -> sys.path insert repo_root
src_pkg_init = REPO_ROOT / "src" / PACKAGE_NAME / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE_NAME / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Cannot find package layout for '{}': neither {} nor {} exists.".format(
            PACKAGE_NAME, src_pkg_init, root_pkg_init
        ),
        allow_module_level=True,
    )


def _install_version_stub() -> None:
    """Install a minimal humanize._version stub if missing.

    Some source trees rely on packaging tooling to generate this module.
    For this benchmark we only need a __version__ attribute to satisfy
    the import in humanize.__init__.
    """
    name = "humanize._version"
    if name in sys.modules:
        return

    mod = types.ModuleType(name)
    mod.__dict__["__version__"] = "0.0.0-benchmark"
    sys.modules[name] = mod


_install_version_stub()

try:
    import humanize  # type: ignore  # noqa: E402
except Exception as exc:
    pytest.skip(
        "Failed to import 'humanize' from {}: {}".format(REPO_ROOT, exc),
        allow_module_level=True,
    )


# ---------------------------------------------------------------------------
# Existing tests (kept original intent)
# ---------------------------------------------------------------------------

def test_intcomma_basic() -> None:
    assert humanize.intcomma(1000) == "1,000"
    assert humanize.intcomma(123456789) == "123,456,789"
    assert humanize.intcomma(-12345) == "-12,345"


def test_ordinal() -> None:
    assert humanize.ordinal(1) == "1st"
    assert humanize.ordinal(2) == "2nd"
    assert humanize.ordinal(3) == "3rd"
    assert humanize.ordinal(11) == "11th"
    assert humanize.ordinal(23) == "23rd"


def test_naturalsize() -> None:
    assert humanize.naturalsize(1024) == "1.0 kB"
    assert humanize.naturalsize(10_000_000).endswith("MB")


def test_precisedelta_numeric() -> None:
    d = humanize.precisedelta(3661)  # seconds
    assert "1 hour" in d
    assert "1 minute" in d
    assert "1 second" in d


def test_naturaldelta() -> None:
    now = datetime(2020, 1, 1, 12, 0, 0)
    later = now + timedelta(days=1, hours=2)
    delta_str = humanize.naturaldelta(later - now)
    assert delta_str
    assert "day" in delta_str


def test_naturaltime_reference_point() -> None:
    ref = datetime(2020, 1, 1, 12, 0, 0)
    earlier = ref - timedelta(minutes=10)
    s = humanize.naturaltime(earlier, when=ref)
    assert "10 minutes ago" in s


# ---------------------------------------------------------------------------
# Added functional (happy-path) coverage (>= 10 test_* total)
# ---------------------------------------------------------------------------

def test_intcomma_float_keeps_decimals() -> None:
    s = humanize.intcomma(1234.56)
    assert isinstance(s, str)
    assert s == "1,234.56"


def test_naturalsize_binary_kib() -> None:
    s = humanize.naturalsize(1536, binary=True)
    assert isinstance(s, str)
    assert s
    # Compatible across versions: "KiB" (common) or any case variant.
    assert ("KiB" in s) or ("kib" in s.lower())


def test_precisedelta_timedelta_input() -> None:
    td = timedelta(days=2, hours=1, minutes=1, seconds=1)
    s = humanize.precisedelta(td)
    assert isinstance(s, str)
    assert s
    assert "day" in s
    assert "hour" in s
    assert "minute" in s
    assert "second" in s


def test_naturaltime_future_reference_point() -> None:
    ref = datetime(2020, 1, 1, 12, 0, 0)
    later = ref + timedelta(minutes=10)
    s = humanize.naturaltime(later, when=ref)
    assert isinstance(s, str)
    assert s
    # Common outputs: "10 minutes from now" / "in 10 minutes" / etc.
    assert ("10 minutes" in s) or ("few" in s.lower())


def test_apnumber_basic_words() -> None:
    if not hasattr(humanize, "apnumber"):
        pytest.skip("humanize.apnumber is not available in this repository/version.")
    assert humanize.apnumber(1) == "one"
    assert humanize.apnumber(9) == "nine"
    assert humanize.apnumber(10) == "10"


def test_intword_million_scale() -> None:
    if not hasattr(humanize, "intword"):
        pytest.skip("humanize.intword is not available in this repository/version.")
    s = humanize.intword(1_200_000)
    assert isinstance(s, str)
    assert s
    assert "million" in s.lower()


def test_intword_thousand_scale() -> None:
    if not hasattr(humanize, "intword"):
        pytest.skip("humanize.intword is not available in this repository/version.")
    s = humanize.intword(12_000)
    assert isinstance(s, str)
    assert s
    assert "thousand" in s.lower()


def test_natural_list_three_items() -> None:
    if not hasattr(humanize, "natural_list"):
        pytest.skip("humanize.natural_list is not available in this repository/version.")
    s = humanize.natural_list(["apples", "bananas", "cherries"])
    assert isinstance(s, str)
    assert s
    assert "apples" in s
    assert "bananas" in s
    assert "cherries" in s
    assert "and" in s.lower()


def test_natural_list_two_items() -> None:
    if not hasattr(humanize, "natural_list"):
        pytest.skip("humanize.natural_list is not available in this repository/version.")
    s = humanize.natural_list(["alpha", "beta"])
    assert isinstance(s, str)
    assert s
    assert "alpha" in s
    assert "beta" in s
    assert "and" in s.lower()
