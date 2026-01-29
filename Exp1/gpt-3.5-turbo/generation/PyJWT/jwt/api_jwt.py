import base64
import json
import hmac
import hashlib
import time

from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidSignatureError,
    DecodeError,
)


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def base64url_decode(input_str: str) -> bytes:
    rem = len(input_str) % 4
    if rem > 0:
        input_str += "=" * (4 - rem)
    try:
        return base64.urlsafe_b64decode(input_str.encode("ascii"))
    except (TypeError, ValueError) as e:
        raise DecodeError("Invalid base64 encoding") from e


def _sign_hs256(msg: bytes, key: bytes) -> bytes:
    return hmac.new(key, msg, hashlib.sha256).digest()


def encode(payload, key, algorithm="HS256", **kwargs):
    if algorithm != "HS256":
        raise NotImplementedError("Only HS256 algorithm is supported")

    headers = {"typ": "JWT", "alg": algorithm}
    if "headers" in kwargs:
        # Allow custom headers to be merged
        headers.update(kwargs["headers"])

    # Prepare header and payload json bytes
    header_json = json.dumps(headers, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    # base64url encode header and payload
    header_b64 = base64url_encode(header_json)
    payload_b64 = base64url_encode(payload_json)

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

    signature = _sign_hs256(signing_input, key.encode() if isinstance(key, str) else key)
    signature_b64 = base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode(token, key, algorithms=None, options=None, leeway=0, **kwargs):
    if algorithms is None:
        algorithms = []
    if options is None:
        options = {}

    if not isinstance(algorithms, (list, tuple)):
        raise DecodeError("algorithms must be a list")

    if not algorithms:
        # If verification is expected (key provided), algorithms must be specified
        if key is not None:
            raise DecodeError("No algorithms specified for decoding")

    parts = token.split(".")
    if len(parts) != 3:
        raise DecodeError("Not enough segments")

    header_b64, payload_b64, signature_b64 = parts

    try:
        header_bytes = base64url_decode(header_b64)
        payload_bytes = base64url_decode(payload_b64)
        signature = base64url_decode(signature_b64)
    except Exception as e:
        raise DecodeError("Invalid token encoding") from e

    try:
        header = json.loads(header_bytes)
    except Exception as e:
        raise DecodeError("Invalid header encoding") from e

    try:
        payload = json.loads(payload_bytes)
    except Exception as e:
        raise DecodeError("Invalid payload encoding") from e

    alg = header.get("alg")
    if alg is None:
        raise DecodeError("Algorithm not specified in header")

    if algorithms and alg not in algorithms:
        raise DecodeError(f"Algorithm not allowed: {alg}")

    # Verify signature if key is provided
    if key is not None:
        if alg != "HS256":
            raise NotImplementedError("Only HS256 algorithm is supported")

        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = _sign_hs256(signing_input, key.encode() if isinstance(key, str) else key)

        if not hmac.compare_digest(expected_sig, signature):
            raise InvalidSignatureError("Signature verification failed")

    # Verify expiration if requested
    verify_exp = options.get("verify_exp", True)
    if verify_exp:
        exp = payload.get("exp")
        if exp is not None:
            now = time.time()
            if now > exp + leeway:
                raise ExpiredSignatureError("Signature has expired")

    return payload