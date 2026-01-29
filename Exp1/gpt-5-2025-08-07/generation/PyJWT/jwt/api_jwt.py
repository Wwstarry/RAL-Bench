import base64
import json
import hmac
import hashlib
import time
import datetime
from typing import Any, Dict, Optional, Union, Iterable

from .exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidAlgorithmError,
)


def _force_bytes(value: Union[str, bytes]) -> bytes:
    if isinstance(value, bytes):
        return value
    elif isinstance(value, str):
        return value.encode("utf-8")
    else:
        raise TypeError("key must be str or bytes")


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: Union[str, bytes]) -> bytes:
    try:
        if isinstance(data, str):
            data_bytes = data.encode("ascii")
        else:
            data_bytes = data
        # Add required padding
        rem = len(data_bytes) % 4
        if rem:
            data_bytes += b"=" * (4 - rem)
        return base64.urlsafe_b64decode(data_bytes)
    except Exception as e:
        raise DecodeError(f"Invalid base64-encoded segment: {e}") from e


def _json_dumps(obj: Any, json_encoder=None) -> bytes:
    if json_encoder is not None:
        text = json.dumps(obj, separators=(",", ":"), cls=json_encoder)
    else:
        text = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    return text.encode("utf-8")


def _json_loads(data: bytes) -> Any:
    try:
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        raise DecodeError(f"Invalid JSON: {e}") from e


def _to_timestamp(value: Any) -> Optional[int]:
    """
    Convert a datetime-like value to a UTC POSIX timestamp (int).
    Supports:
    - int/float (returned as int)
    - datetime.datetime (naive treated as UTC)
    - datetime.date (midnight UTC)
    Returns None if cannot convert.
    """
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, datetime.datetime):
        # Treat naive datetime as UTC
        if value.tzinfo is not None:
            return int(value.timestamp())
        else:
            return int(calendar_timegm(value))
    if isinstance(value, datetime.date):
        dt = datetime.datetime(
            value.year, value.month, value.day, 0, 0, 0
        )
        return int(calendar_timegm(dt))
    return None


def calendar_timegm(dt: datetime.datetime) -> float:
    """
    Convert a naive datetime (assumed UTC) to seconds since the epoch.
    """
    # Equivalent to calendar.timegm(dt.utctimetuple()) without importing calendar
    # Compute POSIX timestamp deterministically for UTC
    epoch = datetime.datetime(1970, 1, 1)
    delta = dt - epoch
    return delta.total_seconds()


def _coerce_claim_datetimes(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert known time-based claims from datetime to numeric timestamp.
    """
    result = dict(payload)
    for claim in ("exp", "iat", "nbf"):
        if claim in result:
            ts = _to_timestamp(result[claim])
            if ts is not None:
                result[claim] = ts
    return result


def _hmac_sign(signing_input: bytes, key: bytes, algorithm: str) -> bytes:
    if algorithm != "HS256":
        raise InvalidAlgorithmError(f"Unsupported algorithm: {algorithm}")
    return hmac.new(key, signing_input, hashlib.sha256).digest()


def _verify_signature(signing_input: bytes, signature: bytes, key: bytes, algorithm: str) -> bool:
    try:
        expected = _hmac_sign(signing_input, key, algorithm)
    except InvalidAlgorithmError:
        # If unsupported, treat as non-matching
        return False
    return hmac.compare_digest(expected, signature)


def encode(
    payload: Dict[str, Any],
    key: Union[str, bytes],
    algorithm: str = "HS256",
    **kwargs: Any,
) -> str:
    """
    Create a JWT from a payload and key using HS256 by default.

    Supported kwargs:
    - headers: optional dict to merge into header
    - json_encoder: optional custom JSON encoder class
    """
    headers = kwargs.get("headers")
    json_encoder = kwargs.get("json_encoder")

    if algorithm != "HS256":
        # Keep behavior minimal; only HS256 supported
        raise InvalidAlgorithmError(f"Unsupported algorithm: {algorithm}")

    # Prepare header
    header: Dict[str, Any] = {"typ": "JWT", "alg": algorithm}
    if isinstance(headers, dict):
        header.update(headers)
        # Ensure alg is consistent with argument
        header["alg"] = algorithm

    # Prepare payload (convert datetime claims)
    coerced_payload = _coerce_claim_datetimes(payload)

    header_segment = _b64url_encode(_json_dumps(header, json_encoder))
    payload_segment = _b64url_encode(_json_dumps(coerced_payload, json_encoder))

    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    key_bytes = _force_bytes(key)

    signature = _hmac_sign(signing_input, key_bytes, algorithm)
    signature_segment = _b64url_encode(signature)

    return f"{header_segment}.{payload_segment}.{signature_segment}"


def decode(
    token: str,
    key: Optional[Union[str, bytes]] = None,
    algorithms: Optional[Iterable[str]] = ("HS256",),
    options: Optional[Dict[str, Any]] = None,
    leeway: Union[int, float, datetime.timedelta] = 0,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Decode a JWT.

    Verification behavior:
    - verify_signature defaults to True (can be disabled via options={'verify_signature': False})
    - verify_exp defaults to True (can be disabled via options={'verify_exp': False})
    - algorithms must be specified when verify_signature is True;
      otherwise DecodeError is raised.

    Supports HS256 only for signing verification.
    """
    if not isinstance(token, str):
        raise DecodeError("Token must be a string")

    # Build options with defaults; accept legacy kwargs like verify and verify_exp
    merged_options: Dict[str, Any] = {
        "verify_signature": True,
        "verify_exp": True,
    }
    if options:
        merged_options.update(options)
    # Legacy kwargs mapping
    if "verify" in kwargs:
        merged_options["verify_signature"] = bool(kwargs["verify"])
    if "verify_exp" in kwargs:
        merged_options["verify_exp"] = bool(kwargs["verify_exp"])

    verify_signature = bool(merged_options.get("verify_signature", True))
    verify_exp = bool(merged_options.get("verify_exp", True))

    # Split into segments
    parts = token.split(".")
    if len(parts) != 3:
        raise DecodeError("Not enough segments (expected 3)")

    header_segment, payload_segment, signature_segment = parts

    header_bytes = _b64url_decode(header_segment)
    payload_bytes = _b64url_decode(payload_segment)
    signature_bytes = _b64url_decode(signature_segment) if signature_segment else b""

    header = _json_loads(header_bytes)
    payload = _json_loads(payload_bytes)

    # Algorithm handling
    alg_in_header = header.get("alg")
    if verify_signature:
        # algorithms must be provided and non-empty
        if not algorithms:
            raise DecodeError("Algorithms must be specified to verify signature")
        allowed_algs = list(algorithms)
        if alg_in_header is None:
            raise DecodeError("Algorithm not specified in header")
        if alg_in_header not in allowed_algs:
            raise DecodeError(f"Algorithm '{alg_in_header}' not in allowed algorithms")
        if alg_in_header != "HS256":
            # We only implement HS256
            raise InvalidAlgorithmError(f"Unsupported algorithm: {alg_in_header}")

        # Verify signature
        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        key_bytes = _force_bytes(key) if key is not None else None
        if key_bytes is None:
            raise DecodeError("Key is required to verify signature")
        if not _verify_signature(signing_input, signature_bytes, key_bytes, alg_in_header):
            raise InvalidSignatureError("Signature verification failed")

    # Claim verification
    if verify_exp and "exp" in payload:
        now = time.time()
        # Compute leeway seconds
        if isinstance(leeway, datetime.timedelta):
            leeway_seconds = leeway.total_seconds()
        else:
            try:
                leeway_seconds = float(leeway)
            except Exception:
                leeway_seconds = 0.0

        exp_val = payload["exp"]
        # Allow numeric types and strings that can be converted
        if isinstance(exp_val, (int, float)):
            exp_ts = float(exp_val)
        else:
            ts = _to_timestamp(exp_val)
            if ts is None:
                # If not a valid timestamp, treat as invalid -> expired
                raise ExpiredSignatureError("Invalid 'exp' claim format")
            exp_ts = float(ts)

        if now > (exp_ts + leeway_seconds):
            raise ExpiredSignatureError("Signature has expired")

    return payload