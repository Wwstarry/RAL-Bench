import base64
import json
import hmac
import hashlib
import time

from .exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidAlgorithmError,
    InvalidSignatureError,
)


def _ensure_bytes(key):
    if isinstance(key, str):
        return key.encode("utf-8")
    return key


def _base64url_encode(input_bytes: bytes) -> bytes:
    return base64.urlsafe_b64encode(input_bytes).rstrip(b"=")


def _base64url_decode(input_str: str) -> bytes:
    input_bytes = input_str.encode("ascii")
    padding = b"=" * (-len(input_bytes) % 4)
    return base64.urlsafe_b64decode(input_bytes + padding)


def encode(payload, key, algorithm="HS256", **kwargs):
    """
    Encodes a payload into a JSON Web Token (JWT).
    """
    if algorithm != "HS256":
        raise NotImplementedError("Only HS256 algorithm is supported")

    # Header
    header = {"alg": algorithm, "typ": "JWT"}
    json_header = json.dumps(
        header, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    encoded_header = _base64url_encode(json_header)

    # Payload
    json_payload = json.dumps(
        payload, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    encoded_payload = _base64url_encode(json_payload)

    # Signature
    signing_input = encoded_header + b"." + encoded_payload
    key_bytes = _ensure_bytes(key)

    signature = hmac.new(key_bytes, signing_input, hashlib.sha256).digest()
    encoded_signature = _base64url_encode(signature)

    # Combine into JWT
    jwt_string = (
        encoded_header + b"." + encoded_payload + b"." + encoded_signature
    ).decode("ascii")

    return jwt_string


def decode(token, key, algorithms=["HS256"], options=None, leeway=0, **kwargs):
    """
    Decodes a JSON Web Token (JWT).
    """
    options = options or {}
    verify_signature = options.get("verify_signature", True)
    verify_exp = options.get("verify_exp", True)

    if not isinstance(token, str):
        raise DecodeError("Invalid token type. Token must be a string.")

    try:
        signing_input, crypto_segment = token.rsplit(".", 1)
        header_segment, payload_segment = signing_input.split(".", 1)
    except ValueError:
        raise DecodeError("Not enough segments")

    # Decode header
    try:
        header_data = _base64url_decode(header_segment)
        header = json.loads(header_data.decode("utf-8"))
    except Exception:
        raise DecodeError("Invalid header padding or JSON")

    if not isinstance(header, dict):
        raise DecodeError("Invalid header format")

    # Decode payload
    try:
        payload_data = _base64url_decode(payload_segment)
        payload = json.loads(payload_data.decode("utf-8"))
    except Exception:
        raise DecodeError("Invalid payload padding or JSON")

    if not isinstance(payload, dict):
        raise DecodeError("Invalid payload format")

    # Signature Verification
    if verify_signature:
        if not algorithms:
            raise DecodeError(
                'It is required that you pass in a value for the "algorithms" '
                "argument when calling decode()."
            )

        header_alg = header.get("alg")
        if header_alg not in algorithms:
            raise InvalidAlgorithmError("Algorithm not allowed")

        if header_alg == "HS256":
            try:
                signature = _base64url_decode(crypto_segment)
            except Exception:
                raise DecodeError("Invalid signature padding")

            key_bytes = _ensure_bytes(key)

            expected_signature = hmac.new(
                key_bytes, signing_input.encode("ascii"), hashlib.sha256
            ).digest()

            if not hmac.compare_digest(signature, expected_signature):
                raise InvalidSignatureError("Signature verification failed")
        else:
            raise InvalidAlgorithmError("Algorithm not supported")

    # Expiration claim verification
    if verify_exp and "exp" in payload:
        try:
            exp_timestamp = int(payload["exp"])
        except (ValueError, TypeError):
            raise DecodeError('"exp" claim must be an integer.')

        current_timestamp = int(time.time())

        if current_timestamp > (exp_timestamp + leeway):
            raise ExpiredSignatureError("Signature has expired")

    return payload