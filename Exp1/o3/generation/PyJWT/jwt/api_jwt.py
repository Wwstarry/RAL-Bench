"""
A very small subset of the original ``PyJWT`` project implementing only
features required by the test-suite shipped with this repository.

Supported algorithms:
    * HS256  (HMAC using SHA-256)

Supported claims:
    * exp    (expiration time)

The public interface intentionally mimics ``PyJWT`` so that existing
code/tests can use ``import jwt`` or ``from jwt import decode, encode``.
No external cryptography libraries are required – only the Python stdlib.
"""

import base64
import json
import time
import hmac
import hashlib
from typing import Any, Dict, List, Optional, Union

from .exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
)

__all__ = ("PyJWT",)


def _b64url_encode(data: bytes) -> bytes:
    """
    Return base64url encoded bytes without padding.
    """
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def _b64url_decode(data: Union[str, bytes]) -> bytes:
    """
    Decode base64url encoded data, adding padding if necessary.
    """
    if isinstance(data, str):
        data_bytes = data.encode("ascii")
    else:
        data_bytes = data
    padding_len = (4 - len(data_bytes) % 4) % 4
    data_bytes += b"=" * padding_len
    try:
        return base64.urlsafe_b64decode(data_bytes)
    except (ValueError, binascii.Error):  # pragma: no cover – binascii only on CPython
        raise DecodeError("Invalid base64-encoded segment encountered")


def _json_dumps(data: Any) -> str:
    """
    Render *data* as a compact JSON string (no whitespace).
    """
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def _sign_hs256(msg: bytes, key: Union[str, bytes]) -> bytes:
    if isinstance(key, str):
        key = key.encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).digest()


def _constant_time_compare(val1: bytes, val2: bytes) -> bool:
    """
    Compare *val1* and *val2* using :func:`hmac.compare_digest`.
    """
    return hmac.compare_digest(val1, val2)


class PyJWT:
    """
    Minimal re-implementation of PyJWT's core API focused on HS256.
    """

    def __init__(self) -> None:
        # Default options inspired by PyJWT
        self.default_options: Dict[str, bool] = {
            "verify_signature": True,
            "verify_exp": True,
        }

    # ------------------------------------------------------------------ encode

    def encode(
        self,
        payload: Dict[str, Any],
        key: Union[str, bytes],
        algorithm: str = "HS256",
        headers: Optional[Dict[str, Any]] = None,
        json_encoder: Optional[json.JSONEncoder] = None,
    ) -> str:
        """
        Create a JSON Web Token.

        Only HS256 (HMAC + SHA-256) is supported. The returned value is
        a ``str`` instance containing the compact JWT.
        """
        algorithm = (algorithm or "").upper()
        if algorithm != "HS256":
            raise NotImplementedError("Only HS256 algorithm is supported in this implementation")

        # Ensure header contains required fields.
        jws_header: Dict[str, Any] = {"alg": "HS256", "typ": "JWT"}
        if headers:
            jws_header.update(headers)

        # Serialise header & payload
        header_segment = _b64url_encode(
            _json_dumps(jws_header).encode("utf-8")
        )
        payload_segment = _b64url_encode(
            _json_dumps(payload).encode("utf-8")
        )

        signing_input = b".".join([header_segment, payload_segment])
        signature = _sign_hs256(signing_input, key)
        signature_segment = _b64url_encode(signature)

        token = b".".join([header_segment, payload_segment, signature_segment])
        return token.decode("ascii")

    # ------------------------------------------------------------------ decode

    def decode(
        self,
        token: Union[str, bytes],
        key: Union[str, bytes] = "",
        algorithms: Optional[List[str]] = None,
        options: Optional[Dict[str, bool]] = None,
        leeway: int = 0,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Decode *token* and return the payload.

        For simplicity only symmetric verification (HS256) is supported.
        """
        if isinstance(token, bytes):
            token = token.decode("ascii")

        # Merge options – kwargs can override `verify_exp` just like PyJWT.
        merged_options = dict(self.default_options)
        if options:
            merged_options.update(options)
        if "verify_exp" in kwargs:
            merged_options["verify_exp"] = kwargs.pop("verify_exp")

        verify_signature = merged_options.get("verify_signature", True)
        verify_exp = merged_options.get("verify_exp", True)

        # PyJWT passes through any additional kwargs, but we ignore them here.
        # This keeps the API compatible.
        if verify_signature and not algorithms:
            raise DecodeError('It is required that you pass in a value for the "algorithms" argument when calling decode().')

        segments = token.split(".")
        if len(segments) != 3:
            raise DecodeError("Not enough segments")

        header_segment, payload_segment, crypto_segment = segments
        try:
            header = json.loads(_b64url_decode(header_segment))
        except Exception as exc:
            raise DecodeError(f"Invalid header encoding: {exc}") from exc

        alg_in_header = header.get("alg")
        if verify_signature:
            if not alg_in_header or alg_in_header not in algorithms:
                raise DecodeError("The specified alg value is not allowed")

        # Decode payload early – needed for 'exp' check even when signature verification disabled.
        try:
            payload = json.loads(_b64url_decode(payload_segment))
        except Exception as exc:
            raise DecodeError(f"Invalid payload encoding: {exc}") from exc

        signing_input = ".".join([header_segment, payload_segment]).encode("ascii")

        if verify_signature and alg_in_header != "none":
            expected_sig = _sign_hs256(signing_input, key)
            try:
                supplied_sig = _b64url_decode(crypto_segment)
            except Exception as exc:
                raise DecodeError(f"Invalid signature encoding: {exc}") from exc

            if not _constant_time_compare(supplied_sig, expected_sig):
                raise InvalidSignatureError("Signature verification failed")

        # Expiration handling
        if verify_exp and "exp" in payload:
            now = int(time.time())
            try:
                exp = int(payload["exp"])
            except Exception:
                raise DecodeError('"exp" claim must be an int')
            if exp + int(leeway) < now:
                raise ExpiredSignatureError("Signature has expired")

        # If verification is off, no further checks are required.
        return payload