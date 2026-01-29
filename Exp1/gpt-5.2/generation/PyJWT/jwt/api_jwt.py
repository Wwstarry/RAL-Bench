import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from .exceptions import DecodeError, ExpiredSignatureError, InvalidSignatureError


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    if isinstance(data, bytes):
        data = data.decode("ascii")
    # Add padding
    rem = len(data) % 4
    if rem:
        data += "=" * (4 - rem)
    try:
        return base64.urlsafe_b64decode(data.encode("ascii"))
    except Exception as e:
        raise DecodeError("Invalid base64url encoding") from e


def _json_dumps(obj: Any) -> str:
    # Match common JWT behavior: compact JSON, deterministic key order for stable output.
    return json.dumps(obj, separators=(",", ":"), sort_keys=True)


def _force_bytes(key: Any) -> bytes:
    if key is None:
        return b""
    if isinstance(key, bytes):
        return key
    if isinstance(key, str):
        return key.encode("utf-8")
    return str(key).encode("utf-8")


def _sign_hs256(signing_input: bytes, key: bytes) -> bytes:
    return hmac.new(key, signing_input, hashlib.sha256).digest()


def encode(
    payload: Dict[str, Any],
    key: Union[str, bytes],
    algorithm: str = "HS256",
    headers: Optional[Dict[str, Any]] = None,
    json_encoder=None,
    **kwargs,
) -> str:
    if algorithm is None:
        algorithm = "HS256"
    if algorithm != "HS256":
        raise NotImplementedError("Only HS256 is supported in this implementation")

    header = {"typ": "JWT", "alg": algorithm}
    if headers:
        header.update(headers)

    if not isinstance(payload, dict):
        raise TypeError("Payload must be a dict")

    header_json = _json_dumps(header).encode("utf-8")
    payload_json = _json_dumps(payload).encode("utf-8")

    segments = [
        _b64url_encode(header_json),
        _b64url_encode(payload_json),
    ]
    signing_input = ".".join(segments).encode("ascii")

    sig = _sign_hs256(signing_input, _force_bytes(key))
    segments.append(_b64url_encode(sig))
    return ".".join(segments)


def _split_token(token: Union[str, bytes]) -> Tuple[str, str, str]:
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    if not isinstance(token, str):
        raise DecodeError("Invalid token type")
    parts = token.split(".")
    if len(parts) != 3:
        raise DecodeError("Not enough segments")
    return parts[0], parts[1], parts[2]


def _load_segment_json(seg_b64: str, name: str) -> Dict[str, Any]:
    raw = _b64url_decode(seg_b64)
    try:
        obj = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise DecodeError(f"Invalid {name} string") from e
    if not isinstance(obj, dict):
        raise DecodeError(f"Invalid {name} type")
    return obj


def decode(
    token: Union[str, bytes],
    key: Union[str, bytes, None] = None,
    algorithms: Optional[List[str]] = None,
    options: Optional[Dict[str, Any]] = None,
    leeway: Union[int, float] = 0,
    **kwargs,
) -> Dict[str, Any]:
    options = dict(options or {})

    # Common PyJWT-ish behavior: if algorithms is not provided, but verification is expected,
    # raise DecodeError. Our tests specifically require this.
    verify_signature = options.get("verify_signature", True)
    if verify_signature and not algorithms:
        raise DecodeError("It is required that you pass in a value for the 'algorithms' argument when calling decode().")

    header_b64, payload_b64, sig_b64 = _split_token(token)
    header = _load_segment_json(header_b64, "header")
    payload = _load_segment_json(payload_b64, "payload")

    alg = header.get("alg")
    if verify_signature:
        if not algorithms:
            raise DecodeError("Missing algorithms")
        if alg not in algorithms:
            raise DecodeError("The specified alg value is not allowed")
        if alg != "HS256":
            raise DecodeError("Unsupported algorithm")

        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = _sign_hs256(signing_input, _force_bytes(key))
        provided_sig = _b64url_decode(sig_b64)

        # Constant-time compare
        if not hmac.compare_digest(expected_sig, provided_sig):
            raise InvalidSignatureError("Signature verification failed")

    # Expiration verification
    verify_exp = options.get("verify_exp", True)
    if verify_exp:
        if "exp" in payload:
            exp = payload.get("exp")
            try:
                exp_val = float(exp)
            except Exception as e:
                raise DecodeError("Expiration Time claim (exp) must be a number") from e
            now = time.time()
            lw = float(leeway or 0)
            if now > exp_val + lw:
                raise ExpiredSignatureError("Signature has expired")

    return payload