from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Dict
import types

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("PYJWT_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "PyJWT"
else:
    REPO_ROOT = ROOT / "generation" / "PyJWT"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _install_cryptography_stub() -> None:
    """
    Install a minimal stub for the 'cryptography' package into sys.modules.

    Same as in functional_test; duplicated here to keep each test file independent.
    """
    crypto = types.ModuleType("cryptography")

    exceptions_mod = types.ModuleType("cryptography.exceptions")

    class UnsupportedAlgorithm(Exception):  # type: ignore[override]
        pass

    class InvalidSignature(Exception):  # type: ignore[override]
        pass

    class _Reasons:  # type: ignore[override]
        UNSUPPORTED_ELLIPTIC_CURVE = "UNSUPPORTED_ELLIPTIC_CURVE"

    exceptions_mod.UnsupportedAlgorithm = UnsupportedAlgorithm
    exceptions_mod.InvalidSignature = InvalidSignature
    exceptions_mod._Reasons = _Reasons

    hazmat_mod = types.ModuleType("cryptography.hazmat")
    primitives_mod = types.ModuleType("cryptography.hazmat.primitives")
    asymmetric_mod = types.ModuleType("cryptography.hazmat.primitives.asymmetric")
    ec_mod = types.ModuleType("cryptography.hazmat.primitives.asymmetric.ec")

    class EllipticCurve:  # type: ignore[override]
        pass

    ec_mod.EllipticCurve = EllipticCurve

    bindings_mod = types.ModuleType("cryptography.hazmat.bindings")
    rust_mod = types.ModuleType("cryptography.hazmat.bindings._rust")
    rust_mod.exceptions = exceptions_mod  # type: ignore[attr-defined]

    sys.modules["cryptography"] = crypto
    sys.modules["cryptography.exceptions"] = exceptions_mod
    sys.modules["cryptography.hazmat"] = hazmat_mod
    sys.modules["cryptography.hazmat.primitives"] = primitives_mod
    sys.modules["cryptography.hazmat.primitives.asymmetric"] = asymmetric_mod
    sys.modules["cryptography.hazmat.primitives.asymmetric.ec"] = ec_mod
    sys.modules["cryptography.hazmat.bindings"] = bindings_mod
    sys.modules["cryptography.hazmat.bindings._rust"] = rust_mod


_install_cryptography_stub()

import jwt  # type: ignore  # noqa: E402


def run_jwt_benchmark(n: int = 2000) -> Dict[str, float]:
    """Sign many JWT tokens and measure performance."""
    key = "perf-key"
    payload = {"v": 123}

    start = time.perf_counter()
    for _ in range(n):
        jwt.encode(payload, key, algorithm="HS256")
    end = time.perf_counter()

    total = end - start

    return {
        "count": float(n),
        "total_time": float(total),
        "tokens_per_second": float(n / total) if total > 0 else 0.0,
    }


def test_jwt_performance_smoke() -> None:
    """Smoke test to ensure the performance benchmark runs successfully."""
    metrics = run_jwt_benchmark(500)
    assert metrics["count"] == 500.0
    assert metrics["total_time"] >= 0.0
    assert metrics["tokens_per_second"] >= 1.0
