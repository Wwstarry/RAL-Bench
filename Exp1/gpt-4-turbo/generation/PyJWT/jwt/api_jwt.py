import json
import base64
import hmac
import hashlib
import time

from .exceptions import (
    ExpiredSignatureError,
    InvalidSignatureError,
    DecodeError,
)

def _base64url_encode(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    encoded = base64.urlsafe_b64encode(data)
    return encoded.rstrip(b'=').decode('ascii')

def _base64url_decode(data):
    if isinstance(data, str):
        data = data.encode("ascii")
    rem = len(data) % 4
    if rem > 0:
        data += b'=' * (4 - rem)
    return base64.urlsafe_b64decode(data)

def _json_encode(obj):
    return json.dumps(obj, separators=(',', ':'), sort_keys=True)

def _json_decode(s):
    return json.loads(s)

def _sign(msg, key, algorithm):
    if algorithm == "HS256":
        return hmac.new(
            key.encode("utf-8") if isinstance(key, str) else key,
            msg.encode("utf-8"),
            hashlib.sha256
        ).digest()
    else:
        raise NotImplementedError("Algorithm not supported: %s" % algorithm)

def _verify_signature(msg, signature, key, algorithm):
    expected_sig = _sign(msg, key, algorithm)
    return hmac.compare_digest(signature, expected_sig)

def encode(payload, key, algorithm="HS256", headers=None, **kwargs):
    if not isinstance(payload, dict):
        raise TypeError("Payload must be a dict")
    if headers is None:
        headers = {}
    headers = dict(headers)  # copy
    headers["typ"] = "JWT"
    headers["alg"] = algorithm

    segments = []
    header_segment = _base64url_encode(_json_encode(headers))
    payload_segment = _base64url_encode(_json_encode(payload))
    signing_input = "%s.%s" % (header_segment, payload_segment)
    signature = _sign(signing_input, key, algorithm)
    signature_segment = _base64url_encode(signature)
    return "%s.%s.%s" % (header_segment, payload_segment, signature_segment)

def decode(token, key=None, algorithms=None, options=None, leeway=0, **kwargs):
    if not isinstance(token, str):
        raise DecodeError("Token must be a string")
    if options is None:
        options = {}
    verify_signature = options.get("verify_signature", True)
    verify_exp = options.get("verify_exp", True)
    # Accept verify_exp from kwargs for compatibility
    if "verify_exp" in kwargs:
        verify_exp = kwargs["verify_exp"]

    parts = token.split('.')
    if len(parts) != 3:
        raise DecodeError("Not enough segments")
    header_b64, payload_b64, signature_b64 = parts

    try:
        header = _json_decode(_base64url_decode(header_b64))
        payload = _json_decode(_base64url_decode(payload_b64))
        signature = _base64url_decode(signature_b64)
    except Exception as e:
        raise DecodeError("Invalid token encoding") from e

    alg = header.get("alg")
    if verify_signature:
        if not algorithms:
            raise DecodeError("Algorithms must be specified for signature verification")
        if alg not in algorithms:
            raise DecodeError("Algorithm %s not in allowed algorithms" % alg)
        if key is None:
            raise DecodeError("Key is required for signature verification")
        signing_input = "%s.%s" % (header_b64, payload_b64)
        if not _verify_signature(signing_input, signature, key, alg):
            raise InvalidSignatureError("Signature verification failed")

    # exp claim
    if verify_exp and "exp" in payload:
        try:
            exp = int(payload["exp"])
        except Exception:
            raise DecodeError("Invalid exp claim")
        now = int(time.time())
        if now > exp + int(leeway):
            raise ExpiredSignatureError("Signature has expired")

    return payload