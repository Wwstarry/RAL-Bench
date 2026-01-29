import json
import time
import hmac
import hashlib
import base64

from .exceptions import DecodeError, ExpiredSignatureError, InvalidSignatureError

def base64url_encode(input_bytes):
    return base64.urlsafe_b64encode(input_bytes).rstrip(b'=').decode('ascii')

def base64url_decode(input_str):
    rem = len(input_str) % 4
    if rem > 0:
        input_str += '=' * (4 - rem)
    return base64.urlsafe_b64decode(input_str)

def encode(payload, key, algorithm="HS256", **kwargs):
    if algorithm != "HS256":
        # Only HS256 is supported in this simple implementation
        raise NotImplementedError("Only HS256 is supported")

    header = {"alg": algorithm, "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":"), sort_keys=True)
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    header_b64 = base64url_encode(header_json.encode("utf-8"))
    payload_b64 = base64url_encode(payload_json.encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}"

    # HS256 signature
    signature = hmac.new(
        key.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256
    ).digest()
    signature_b64 = base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"

def decode(token, key, algorithms=["HS256"], options=None, leeway=0, **kwargs):
    if not algorithms:
        raise DecodeError("No algorithms specified for decoding")

    parts = token.split(".")
    if len(parts) != 3:
        raise DecodeError("Not enough segments in token")

    header_b64, payload_b64, signature_b64 = parts

    try:
        header_data = base64url_decode(header_b64)
        header = json.loads(header_data)
        payload_data = base64url_decode(payload_b64)
        payload = json.loads(payload_data)
    except Exception:
        raise DecodeError("Invalid token formatting")

    if header.get("alg") not in algorithms:
        raise DecodeError("Algorithm not allowed")

    # Verify signature
    signing_input = f"{header_b64}.{payload_b64}"
    expected_sig = hmac.new(
        key.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256
    ).digest()
    sig_to_verify = base64url_decode(signature_b64)

    if not hmac.compare_digest(expected_sig, sig_to_verify):
        raise InvalidSignatureError("Signature verification failed")

    # Check expiration
    verify_exp = True
    if options and isinstance(options, dict):
        verify_exp = options.get("verify_exp", True)

    if verify_exp and "exp" in payload:
        now = time.time()
        exp = payload["exp"]
        if now > exp + leeway:
            raise ExpiredSignatureError("Signature has expired")

    return payload