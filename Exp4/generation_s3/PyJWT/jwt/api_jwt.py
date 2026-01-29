import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional

from .exceptions import DecodeError, ExpiredSignatureError, InvalidSignatureError


def _to_bytes(key: Any) -> bytes:
    if key is None:
        return b""
    if isinstance(key, bytes):
        return key
    if isinstance(key, str):
        return key.encode("utf-8")
    # Fallback: try string conversion
    return str(key).encode("utf-8")


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    if not isinstance(data, str):
        raise DecodeError("Invalid token segment type")
    s = data.encode("ascii")
    # restore padding
    pad = b"=" * ((4 - (len(s) % 4)) % 4)
    try:
        return base64.urlsafe_b64decode(s + pad)
    except Exception as e:  # noqa: BLE001
        raise DecodeError("Invalid base64") from e


def _json_dumps(obj: Any, json_encoder=None) -> str:
    kwargs = {"separators": (",", ":"), "sort_keys": True}
    if json_encoder is not None:
        kwargs["cls"] = json_encoder
    return json.dumps(obj, **kwargs)


def _json_loads(data: bytes) -> Any:
    try:
        return json.loads(data.decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        raise DecodeError("Invalid JSON") from e


class PyJWT:
    def encode(
        self,
        payload: Dict[str, Any],
        key: Any,
        algorithm: str = "HS256",
        headers: Optional[Dict[str, Any]] = None,
        json_encoder=None,
        **kwargs,
    ) -> str:
        if algorithm is None:
            algorithm = "HS256"
        if algorithm != "HS256":
            raise DecodeError("Unsupported algorithm")

        header = {"typ": "JWT", "alg": algorithm}
        if headers:
            # allow user-supplied headers to override/add
            header.update(headers)

        header_b64 = _b64url_encode(_json_dumps(header, json_encoder=json_encoder).encode("utf-8"))
        payload_b64 = _b64url_encode(_json_dumps(payload, json_encoder=json_encoder).encode("utf-8"))

        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        mac = hmac.new(_to_bytes(key), signing_input, hashlib.sha256).digest()
        sig_b64 = _b64url_encode(mac)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    def decode(
        self,
        jwt: str,
        key: Any = "",
        algorithms=None,
        options: Optional[Dict[str, Any]] = None,
        leeway: float = 0,
        **kwargs,
    ) -> Dict[str, Any]:
        if not isinstance(jwt, str):
            raise DecodeError("Invalid token type")

        options = options or {}
        verify_signature = options.get("verify_signature", True)
        verify_exp = options.get("verify_exp", True)

        parts = jwt.split(".")
        if len(parts) != 3:
            raise DecodeError("Not enough segments")

        header_b64, payload_b64, sig_b64 = parts

        header_bytes = _b64url_decode(header_b64)
        payload_bytes = _b64url_decode(payload_b64)
        signature = _b64url_decode(sig_b64)

        header = _json_loads(header_bytes)
        payload = _json_loads(payload_bytes)

        if not isinstance(header, dict) or not isinstance(payload, dict):
            raise DecodeError("Invalid header or payload")

        alg = header.get("alg")
        if alg is None:
            raise DecodeError("Missing alg")

        if verify_signature:
            if algorithms is None:
                raise DecodeError('It is required that you pass in a value for the "algorithms" argument when calling decode().')

            # accept string or iterable; tests typically pass a list
            if isinstance(algorithms, (str, bytes)):
                alg_list = [algorithms.decode("utf-8") if isinstance(algorithms, bytes) else algorithms]
            else:
                try:
                    alg_list = list(algorithms)
                except TypeError as e:
                    raise DecodeError("Invalid algorithms") from e

            if "HS256" not in alg_list:
                raise DecodeError("The specified alg value is not allowed")

            if alg != "HS256":
                raise DecodeError("Unsupported algorithm")

            signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
            expected = hmac.new(_to_bytes(key), signing_input, hashlib.sha256).digest()
            if not hmac.compare_digest(expected, signature):
                raise InvalidSignatureError("Signature verification failed")

        if verify_exp and "exp" in payload:
            exp = payload.get("exp")
            try:
                if isinstance(exp, str):
                    exp_val = float(exp)
                elif isinstance(exp, (int, float)):
                    exp_val = float(exp)
                else:
                    # try coercion
                    exp_val = float(exp)
            except Exception as e:  # noqa: BLE001
                raise DecodeError("Invalid exp claim") from e

            now = time.time()
            try:
                leeway_val = float(leeway or 0)
            except Exception as e:  # noqa: BLE001
                raise DecodeError("Invalid leeway") from e

            if now > exp_val + leeway_val:
                raise ExpiredSignatureError("Signature has expired")

        return payload