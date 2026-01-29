import base64
import json
import hmac
import hashlib
import time
from .exceptions import ExpiredSignatureError, InvalidSignatureError, DecodeError

def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def base64url_decode(data):
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def encode(payload, key, algorithm="HS256", **kwargs):
    if algorithm != "HS256":
        raise NotImplementedError("Only HS256 is supported in this implementation.")
    
    header = {"alg": algorithm, "typ": "JWT"}
    header_b64 = base64url_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = base64url_encode(json.dumps(payload).encode("utf-8"))
    
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = base64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"

def decode(token, key, algorithms=["HS256"], options=None, leeway=0, **kwargs):
    if not algorithms or "HS256" not in algorithms:
        raise DecodeError("Algorithm not specified or unsupported.")
    
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError:
        raise DecodeError("Invalid token format.")
    
    try:
        header = json.loads(base64url_decode(header_b64).decode("utf-8"))
        payload = json.loads(base64url_decode(payload_b64).decode("utf-8"))
        signature = base64url_decode(signature_b64)
    except (ValueError, json.JSONDecodeError):
        raise DecodeError("Invalid token encoding.")
    
    if header.get("alg") != "HS256":
        raise DecodeError("Algorithm mismatch.")
    
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_signature = hmac.new(key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    
    if not hmac.compare_digest(signature, expected_signature):
        raise InvalidSignatureError("Signature verification failed.")
    
    if "exp" in payload:
        exp = payload["exp"]
        current_time = time.time()
        if current_time > exp + leeway:
            raise ExpiredSignatureError("Token has expired.")
    
    return payload