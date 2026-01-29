import base64
import binascii
import json
import hmac
import hashlib
import time

from .exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
)


def b64url_encode(data: bytes) -> bytes:
    """URL-safe base64 encoding, without padding."""
    return base64.urlsafe_b64encode(data).replace(b"=", b"")


def b64url_decode(data: bytes) -> bytes:
    """URL-safe base64 decoding, with padding added back."""
    try:
        padding = b"=" * (4 - (len(data) % 4))
        return base64.urlsafe_b64decode(data + padding)
    except (ValueError, binascii.Error):
        raise DecodeError("Invalid base64 encoding")


def encode(payload, key, algorithm="HS256", **kwargs):
    if algorithm != "HS256":
        raise NotImplementedError("Only HS256 algorithm is supported")

    header = {"alg": "HS256", "typ": "JWT"}
    json_header = json.dumps(
        header, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    json_payload = json.dumps(
        payload, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")

    b64_header = b64url_encode(json_header)
    b64_payload = b64url_encode(json_payload)

    signing_input = b64_header + b"." + b64_payload

    if isinstance(key, str):
        key = key.encode("utf-8")

    signature = hmac.new(key, signing_input, hashlib.sha256).digest()
    b64_signature = b64url_encode(signature)

    token = signing_input + b"." + b64_signature
    return token.decode("utf-8")


def decode(token, key, algorithms=["HS256"], options=None, leeway=0, **kwargs):
    if isinstance(token, str):
        token = token.encode("utf-8")

    try:
        signing_input, crypto_segment = token.rsplit(b".", 1)
        header_segment, payload_segment = signing_input.split(b".", 1)
    except ValueError:
        raise DecodeError("Not enough segments")

    # Header
    try:
        header_data = b64url_decode(header_segment)
        header = json.loads(header_data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise DecodeError("Invalid header: non-JSON or non-UTF8 content")

    # Payload
    try:
        payload_data = b64url_decode(payload_segment)
        payload = json.loads(payload_data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise DecodeError("Invalid payload: non-JSON or non-UTF8 content")

    # Signature
    signature = b64url_decode(crypto_segment)

    # Verification
    if key is not None:
        if not algorithms:
            raise DecodeError("Algorithms must be specified when a key is provided")

        alg = header.get("alg")
        if alg not in algorithms:
            raise InvalidSignatureError(f"Algorithm {alg} is not allowed")

        if alg == "HS256":
            if isinstance(key, str):
                key = key.encode("utf-8")

            expected_signature = hmac.new(
                key, signing_input, hashlib.sha256
            ).digest()
            if not hmac.compare_digest(signature, expected_signature):
                raise InvalidSignatureError("Signature verification failed")
        else:
            raise NotImplementedError(f"Algorithm {alg} not supported")

    # Claim verification
    options = options or {}
    verify_exp = options.get("verify_exp", True)

    if verify_exp and "exp" in payload:
        try:
            exp_time = int(payload["exp"])
        except (ValueError, TypeError):
            raise DecodeError('"exp" claim must be an integer.')

        current_time = time.time()
        if exp_time < current_time - leeway:
            raise ExpiredSignatureError("Signature has expired")

    return payload