import base64
import hmac
import hashlib
import json
import time
from typing import Dict, List, Optional, Any

from .exceptions import DecodeError, ExpiredSignatureError, InvalidSignatureError


def base64url_encode(data: bytes) -> str:
    """Encode bytes using base64url encoding without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def base64url_decode(data: str) -> bytes:
    """Decode a base64url encoded string without padding."""
    padding = '=' * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def encode(
    payload: Dict[str, Any],
    key: str,
    algorithm: str = "HS256",
    **kwargs
) -> str:
    """
    Encode a JWT with the given payload, key and algorithm.

    Args:
        payload: The JWT payload to encode.
        key: The secret key used for signing.
        algorithm: The algorithm to use for signing. Currently only HS256 is supported.
        **kwargs: Additional options (not used in this implementation).

    Returns:
        A string representing the encoded JWT.
    """
    if algorithm != "HS256":
        raise NotImplementedError(f"Algorithm {algorithm} not supported")
    
    # Create the header
    header = {"typ": "JWT", "alg": algorithm}
    
    # Encode header and payload
    header_part = base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_part = base64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    
    # Create the message to sign
    message = f"{header_part}.{payload_part}"
    
    # Sign the message with HMAC-SHA256
    signature = hmac.new(
        key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature_part = base64url_encode(signature)
    
    # Return the complete JWT
    return f"{message}.{signature_part}"


def decode(
    token: str,
    key: Optional[str] = None,
    algorithms: Optional[List[str]] = None,
    options: Optional[Dict[str, bool]] = None,
    leeway: int = 0,
    **kwargs
) -> Dict[str, Any]:
    """
    Decode a JWT and validate its signature if required.

    Args:
        token: The JWT string to decode.
        key: The secret key used to check the signature.
        algorithms: List of allowed algorithms. Currently only ["HS256"] is supported.
        options: Dict of options for controlling validation behavior.
        leeway: Number of seconds of clock skew allowed when verifying exp claims.
        **kwargs: Additional options (not used in this implementation).

    Returns:
        The decoded JWT payload as a dictionary.

    Raises:
        DecodeError: If the token is invalid or the algorithm is not supported.
        InvalidSignatureError: If signature verification fails.
        ExpiredSignatureError: If the token has expired.
    """
    if algorithms is None:
        raise DecodeError("Missing algorithms")
    
    if options is None:
        options = {"verify_signature": True, "verify_exp": True}
    
    # Parse the token
    try:
        header_part, payload_part, signature_part = token.split('.')
    except ValueError:
        raise DecodeError("Not enough segments")
    
    # Decode the header and payload
    try:
        header = json.loads(base64url_decode(header_part).decode('utf-8'))
        payload = json.loads(base64url_decode(payload_part).decode('utf-8'))
    except Exception:
        raise DecodeError("Invalid token")
    
    # Verify the algorithm
    if header.get('alg') not in algorithms:
        raise DecodeError(f"Algorithm {header.get('alg')} not supported")
    
    # Verify signature if required
    if options.get("verify_signature", True) and key is not None:
        message = f"{header_part}.{payload_part}"
        expected_signature = hmac.new(
            key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        try:
            actual_signature = base64url_decode(signature_part)
            if not hmac.compare_digest(actual_signature, expected_signature):
                raise InvalidSignatureError("Signature verification failed")
        except Exception:
            raise InvalidSignatureError("Signature verification failed")
    
    # Check expiration if required
    if options.get("verify_exp", True) and 'exp' in payload:
        now = int(time.time())
        if payload['exp'] < (now - leeway):
            raise ExpiredSignatureError("Token has expired")
    
    return payload