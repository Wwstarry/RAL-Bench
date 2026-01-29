import json
import base64
import hmac
import hashlib
import time
from typing import Any, Dict, List, Optional

from .exceptions import (
    ExpiredSignatureError,
    InvalidSignatureError,
    DecodeError,
)


def _base64url_encode(data: bytes) -> str:
    """Base64URL encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _base64url_decode(data: str) -> bytes:
    """Base64URL decode with padding added if needed."""
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def _sign(msg: bytes, key: str, algorithm: str) -> str:
    """Create HMAC signature."""
    if algorithm != "HS256":
        raise DecodeError("Algorithm not supported")
    
    key_bytes = key.encode('utf-8') if isinstance(key, str) else key
    signature = hmac.new(key_bytes, msg, hashlib.sha256).digest()
    return _base64url_encode(signature)


def _verify_signature(msg: bytes, sig: str, key: str, algorithm: str) -> bool:
    """Verify HMAC signature."""
    expected_sig = _sign(msg, key, algorithm)
    return hmac.compare_digest(expected_sig, sig)


def encode(
    payload: Dict[str, Any],
    key: str,
    algorithm: str = "HS256",
    **kwargs: Any
) -> str:
    """Encode a JWT token."""
    # Create header
    header = {"alg": algorithm, "typ": "JWT"}
    header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
    header_b64 = _base64url_encode(header_json)
    
    # Prepare payload
    payload = payload.copy()
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    payload_b64 = _base64url_encode(payload_json)
    
    # Create signature
    msg = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = _sign(msg, key, algorithm)
    
    return f"{header_b64}.{payload_b64}.{signature}"


def decode(
    token: str,
    key: str,
    algorithms: List[str],
    options: Optional[Dict[str, Any]] = None,
    leeway: int = 0,
    **kwargs: Any
) -> Dict[str, Any]:
    """Decode and verify a JWT token."""
    if options is None:
        options = {}
    
    verify_exp = options.get('verify_exp', True)
    
    # Split token
    parts = token.split('.')
    if len(parts) != 3:
        raise DecodeError("Invalid token structure")
    
    header_b64, payload_b64, signature = parts
    
    # Decode header
    try:
        header_json = _base64url_decode(header_b64)
        header = json.loads(header_json)
    except (ValueError, TypeError, UnicodeDecodeError):
        raise DecodeError("Invalid header")
    
    # Check algorithm
    alg = header.get('alg')
    if alg not in algorithms:
        raise DecodeError("Algorithm not allowed")
    
    # Verify signature if key is provided
    if key is not None and algorithms:
        msg = f"{header_b64}.{payload_b64}".encode('utf-8')
        if not _verify_signature(msg, signature, key, alg):
            raise InvalidSignatureError("Signature verification failed")
    elif not algorithms:
        raise DecodeError("No algorithms specified for verification")
    
    # Decode payload
    try:
        payload_json = _base64url_decode(payload_b64)
        payload = json.loads(payload_json)
    except (ValueError, TypeError, UnicodeDecodeError):
        raise DecodeError("Invalid payload")
    
    # Verify expiration
    if verify_exp and 'exp' in payload:
        exp = payload['exp']
        if not isinstance(exp, (int, float)):
            raise DecodeError("Invalid exp claim")
        
        current_time = time.time()
        if current_time > exp + leeway:
            raise ExpiredSignatureError("Signature has expired")
    
    return payload