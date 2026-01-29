import json
import base64
import hmac
import hashlib
import time
from typing import Any, Dict, List, Optional, Union

from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidAlgorithmError,
)


def _base64url_encode(data: bytes) -> str:
    """Encode bytes to base64url string without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data: str) -> bytes:
    """Decode base64url string to bytes, adding padding if needed."""
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def _ensure_bytes(data: Union[str, bytes]) -> bytes:
    """Convert string to bytes if needed."""
    if isinstance(data, str):
        return data.encode("utf-8")
    return data


def _sign_hs256(message: bytes, key: Union[str, bytes]) -> bytes:
    """Sign a message using HMAC-SHA256."""
    key_bytes = _ensure_bytes(key)
    return hmac.new(key_bytes, message, hashlib.sha256).digest()


def _verify_hs256(message: bytes, signature: bytes, key: Union[str, bytes]) -> bool:
    """Verify an HMAC-SHA256 signature."""
    key_bytes = _ensure_bytes(key)
    expected_signature = hmac.new(key_bytes, message, hashlib.sha256).digest()
    return hmac.compare_digest(signature, expected_signature)


def encode(
    payload: Dict[str, Any],
    key: Union[str, bytes],
    algorithm: str = "HS256",
    headers: Optional[Dict[str, Any]] = None,
    json_encoder: Optional[type] = None,
    **kwargs
) -> str:
    """
    Encode a JWT token.
    
    Args:
        payload: Dictionary containing the claims to encode
        key: Secret key for signing
        algorithm: Algorithm to use for signing (default: HS256)
        headers: Optional dictionary of additional header fields
        json_encoder: Optional custom JSON encoder class
        **kwargs: Additional arguments (ignored for compatibility)
    
    Returns:
        Encoded JWT token as a string
    
    Raises:
        InvalidAlgorithmError: If algorithm is not supported
    """
    if algorithm != "HS256":
        raise InvalidAlgorithmError(f"Algorithm {algorithm} is not supported")
    
    # Create header
    header = {"typ": "JWT", "alg": algorithm}
    if headers:
        header.update(headers)
    
    # Encode header and payload
    header_bytes = json.dumps(header, separators=(",", ":"), cls=json_encoder).encode("utf-8")
    payload_bytes = json.dumps(payload, separators=(",", ":"), cls=json_encoder).encode("utf-8")
    
    header_b64 = _base64url_encode(header_bytes)
    payload_b64 = _base64url_encode(payload_bytes)
    
    # Create signing input
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    
    # Sign
    signature = _sign_hs256(signing_input, key)
    signature_b64 = _base64url_encode(signature)
    
    # Return complete token
    return f"{signing_input.decode('utf-8')}.{signature_b64}"


def decode(
    token: str,
    key: Union[str, bytes],
    algorithms: Optional[List[str]] = None,
    options: Optional[Dict[str, Any]] = None,
    leeway: Union[int, float] = 0,
    **kwargs
) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string to decode
        key: Secret key for verification
        algorithms: List of allowed algorithms (default: ["HS256"])
        options: Dictionary of verification options
        leeway: Leeway in seconds for expiration verification
        **kwargs: Additional arguments (ignored for compatibility)
    
    Returns:
        Decoded payload as a dictionary
    
    Raises:
        DecodeError: If token format is invalid
        InvalidSignatureError: If signature verification fails
        ExpiredSignatureError: If token has expired
    """
    if algorithms is None:
        algorithms = ["HS256"]
    
    if options is None:
        options = {}
    
    # Set default verification options
    verify_signature = options.get("verify_signature", True)
    verify_exp = options.get("verify_exp", True)
    
    # Split token
    parts = token.split(".")
    if len(parts) != 3:
        raise DecodeError("Invalid token format")
    
    header_b64, payload_b64, signature_b64 = parts
    
    try:
        # Decode header and payload
        header_bytes = _base64url_decode(header_b64)
        payload_bytes = _base64url_decode(payload_b64)
        signature_bytes = _base64url_decode(signature_b64)
        
        header = json.loads(header_bytes.decode("utf-8"))
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (ValueError, TypeError) as e:
        raise DecodeError(f"Invalid token encoding: {e}")
    
    # Check algorithm
    alg = header.get("alg")
    if alg not in algorithms:
        raise DecodeError(f"Algorithm {alg} not in allowed algorithms {algorithms}")
    
    # Verify signature if requested
    if verify_signature:
        if alg == "HS256":
            signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
            if not _verify_hs256(signing_input, signature_bytes, key):
                raise InvalidSignatureError("Signature verification failed")
        else:
            raise InvalidAlgorithmError(f"Algorithm {alg} is not supported")
    
    # Verify expiration if requested
    if verify_exp and "exp" in payload:
        exp = payload["exp"]
        now = time.time()
        if now > exp + leeway:
            raise ExpiredSignatureError("Token has expired")
    
    return payload