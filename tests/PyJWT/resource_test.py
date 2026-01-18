from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import types

import pytest

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

    Same as in the other PyJWT tests to keep behavior consistent.
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


def test_verify_options() -> None:
    """Decoding with verify_exp=True should accept non-expired tokens."""
    key = "secret"
    payload = {
        "foo": "bar",
        "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=10),
    }

    token = jwt.encode(payload, key, algorithm="HS256")

    decoded = jwt.decode(token, key, algorithms=["HS256"], options={"verify_exp": True})

    assert decoded["foo"] == "bar"


def test_leeway() -> None:
    """Leeway should allow slightly expired tokens to still be accepted."""
    key = "secret"
    expired = datetime.now(tz=timezone.utc) - timedelta(seconds=2)

    token = jwt.encode({"exp": expired}, key, algorithm="HS256")

    decoded = jwt.decode(
        token,
        key,
        algorithms=["HS256"],
        options={"verify_exp": True},
        leeway=5,
    )

    assert "exp" in decoded


def test_missing_key() -> None:
    """Invalid token format or wrong key should raise an exception."""
    with pytest.raises(Exception):
        jwt.decode("invalid.token.here", "wrong", algorithms=["HS256"])
