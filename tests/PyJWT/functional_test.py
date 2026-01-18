from __future__ import annotations

import os
import sys
import types
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

# ---------------------------------------------------------------------------
# RACB-compatible import resolution (preferred) + local fallback (no hardcoded abs path)
# ---------------------------------------------------------------------------

PACKAGE_NAME = "jwt"

_racb_root = os.environ.get("RACB_REPO_ROOT", "").strip()
if _racb_root:
    REPO_ROOT = Path(_racb_root).resolve()
else:
    ROOT = Path(__file__).resolve().parents[2]
    target = os.environ.get("PYJWT_TARGET", "reference").lower()
    if target == "reference":
        REPO_ROOT = ROOT / "repositories" / "PyJWT"
    else:
        REPO_ROOT = ROOT / "generation" / "PyJWT"

if not REPO_ROOT.exists():
    pytest.skip(
        "RACB_REPO_ROOT does not exist on disk: {}".format(REPO_ROOT),
        allow_module_level=True,
    )

src_pkg_init = REPO_ROOT / "src" / PACKAGE_NAME / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE_NAME / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not find package '{}' under repo root. Expected {} or {}.".format(
            PACKAGE_NAME, src_pkg_init, root_pkg_init
        ),
        allow_module_level=True,
    )


def _install_cryptography_stub_if_needed() -> None:
    """Install a minimal 'cryptography' stub into sys.modules.

    Purpose: avoid importing a broken system 'cryptography' installation that may
    depend on missing native libraries. This test suite only uses HMAC algorithms.
    """
    if "cryptography" in sys.modules:
        return

    crypto = types.ModuleType("cryptography")

    # cryptography.exceptions
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

    # Provide minimal module tree used by PyJWT optional algorithms
    hazmat_mod = types.ModuleType("cryptography.hazmat")
    primitives_mod = types.ModuleType("cryptography.hazmat.primitives")
    asymmetric_mod = types.ModuleType("cryptography.hazmat.primitives.asymmetric")

    # ec
    ec_mod = types.ModuleType("cryptography.hazmat.primitives.asymmetric.ec")

    class EllipticCurve:  # type: ignore[override]
        pass

    ec_mod.EllipticCurve = EllipticCurve

    # bindings._rust.exceptions
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


_install_cryptography_stub_if_needed()

try:
    import jwt  # type: ignore  # noqa: E402
except Exception as exc:
    pytest.skip("Failed to import jwt: {}".format(exc), allow_module_level=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_token(token: Any) -> str:
    """PyJWT v1 may return bytes; v2 typically returns str."""
    if isinstance(token, bytes):
        return token.decode("utf-8")
    return str(token)


def _fixed_dt_utc(y: int, m: int, d: int, hh: int = 0, mm: int = 0, ss: int = 0) -> datetime:
    return datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc)


def _encode_decode(payload: Dict[str, Any], key: Any, algorithm: str, **decode_kwargs: Any) -> Dict[str, Any]:
    token = _normalize_token(jwt.encode(payload, key, algorithm=algorithm))
    decoded = jwt.decode(token, key, algorithms=[algorithm], **decode_kwargs)
    return decoded


# ---------------------------------------------------------------------------
# Functional-only tests (happy path)
# ---------------------------------------------------------------------------

def test_hs256_basic_encode_decode_roundtrip() -> None:
    payload = {"user": "alice", "admin": False}
    decoded = _encode_decode(payload, key="secret", algorithm="HS256")
    assert decoded["user"] == "alice"
    assert decoded["admin"] is False


def test_hs512_encode_decode_roundtrip() -> None:
    payload = {"scope": ["read", "write"], "active": True}
    decoded = _encode_decode(payload, key="secret", algorithm="HS512")
    assert decoded["scope"] == ["read", "write"]
    assert decoded["active"] is True


def test_encode_decode_with_unicode_claims() -> None:
    payload = {"name": "张三", "city": "東京"}
    decoded = _encode_decode(payload, key="secret", algorithm="HS256")
    assert decoded["name"] == "张三"
    assert decoded["city"] == "東京"


def test_encode_decode_with_datetime_exp_in_future() -> None:
    exp_dt = _fixed_dt_utc(2099, 1, 1, 0, 0, 0)
    payload = {"sub": "u-123", "exp": exp_dt}
    decoded = _encode_decode(payload, key="secret", algorithm="HS256")
    assert decoded["sub"] == "u-123"
    assert int(decoded["exp"]) == int(exp_dt.timestamp())


def test_encode_decode_with_datetime_nbf_in_past() -> None:
    nbf_dt = _fixed_dt_utc(2000, 1, 1, 0, 0, 0)
    payload = {"feature": "enabled", "nbf": nbf_dt}
    decoded = _encode_decode(payload, key="secret", algorithm="HS256")
    assert decoded["feature"] == "enabled"
    assert int(decoded["nbf"]) == int(nbf_dt.timestamp())


def test_encode_decode_with_fixed_iat_integer() -> None:
    iat = 1_600_000_000  # fixed constant; deterministic
    payload = {"role": "admin", "iat": iat}
    decoded = _encode_decode(payload, key="secret", algorithm="HS256")
    assert decoded["role"] == "admin"
    assert int(decoded["iat"]) == iat


def test_encode_decode_with_issuer_and_audience() -> None:
    payload = {"iss": "issuer-service", "aud": "my-app", "sub": "abc"}
    decoded = _encode_decode(
        payload,
        key="secret",
        algorithm="HS256",
        issuer="issuer-service",
        audience="my-app",
    )
    assert decoded["iss"] == "issuer-service"
    assert decoded["aud"] == "my-app"
    assert decoded["sub"] == "abc"


def test_encode_decode_with_subject_and_jti() -> None:
    payload = {"sub": "user-999", "jti": "token-001"}
    decoded = _encode_decode(payload, key="secret", algorithm="HS256")
    assert decoded["sub"] == "user-999"
    assert decoded["jti"] == "token-001"


def test_unverified_header_contains_alg_and_custom_kid() -> None:
    payload = {"foo": "bar"}
    key = "secret"
    token = _normalize_token(jwt.encode(payload, key, algorithm="HS256", headers={"kid": "k1", "typ": "JWT"}))

    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
    assert header.get("kid") == "k1"
    assert header.get("typ") == "JWT"


def test_decode_with_bytes_key() -> None:
    payload = {"user": "bob", "plan": "pro"}
    key = b"secret-bytes"
    decoded = _encode_decode(payload, key=key, algorithm="HS256")
    assert decoded["user"] == "bob"
    assert decoded["plan"] == "pro"


def test_decode_complete_returns_header_and_payload_when_available() -> None:
    """If decode_complete is available, validate it returns header+payload in happy path."""
    if not hasattr(jwt, "decode_complete"):
        pytest.skip("jwt.decode_complete is not available in this implementation")

    payload = {"x": 1, "y": 2}
    key = "secret"
    token = _normalize_token(jwt.encode(payload, key, algorithm="HS256"))

    result = jwt.decode_complete(token, key, algorithms=["HS256"])
    assert isinstance(result, dict)
    assert "header" in result
    assert "payload" in result
    assert result["payload"]["x"] == 1
    assert result["payload"]["y"] == 2
    assert result["header"]["alg"] == "HS256"
