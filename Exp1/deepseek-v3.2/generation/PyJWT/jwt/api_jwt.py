"""
Core JWT API implementation
"""
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
    """Encode data using URL-safe base64 without padding"""
    return base64.urlsafe_b64encode(data).rstrip(b'=')

def _base64url_decode(data):
    """Decode URL-safe base64 without padding"""
    # Add padding if needed
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += b'=' * padding
    return base64.urlsafe_b64decode(data)

def _to_bytes(value):
    """Convert string to bytes if needed"""
    if isinstance(value, str):
        return value.encode('utf-8')
    return value

def encode(payload, key, algorithm="HS256", **kwargs):
    """
    Encode a payload into a JWT token
    
    Args:
        payload: Dictionary containing the claims
        key: Secret key for signing
        algorithm: Signing algorithm (only HS256 supported)
        **kwargs: Additional options
    
    Returns:
        str: Encoded JWT token
    """
    if algorithm != "HS256":
        raise ValueError(f"Algorithm {algorithm} not supported")
    
    # Create header
    header = {
        "typ": "JWT",
        "alg": algorithm
    }
    
    # Convert payload to dict if needed
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dictionary")
    
    # Make a copy to avoid modifying the original
    payload = payload.copy()
    
    # Add iat claim if not present
    if 'iat' not in payload and kwargs.get('add_iat', True):
        payload['iat'] = int(time.time())
    
    # Encode header and payload
    header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    
    header_b64 = _base64url_encode(header_json)
    payload_b64 = _base64url_encode(payload_json)
    
    # Create signing input
    signing_input = header_b64 + b'.' + payload_b64
    
    # Create signature
    key_bytes = _to_bytes(key)
    if algorithm == "HS256":
        signature = hmac.new(key_bytes, signing_input, hashlib.sha256).digest()
    else:
        raise ValueError(f"Algorithm {algorithm} not supported")
    
    signature_b64 = _base64url_encode(signature)
    
    # Return complete token
    return (signing_input + b'.' + signature_b64).decode('utf-8')

def decode(token, key, algorithms=["HS256"], options=None, leeway=0, **kwargs):
    """
    Decode and verify a JWT token
    
    Args:
        token: JWT token string
        key: Secret key for verification
        algorithms: List of allowed algorithms (only ["HS256"] supported)
        options: Dictionary of verification options
        leeway: Number of seconds of leeway for expiration validation
        **kwargs: Additional options
    
    Returns:
        dict: Decoded payload
    
    Raises:
        DecodeError: If token cannot be decoded
        InvalidSignatureError: If signature verification fails
        ExpiredSignatureError: If token has expired
    """
    if options is None:
        options = {}
    
    # Default verification options
    verify_signature = options.get('verify_signature', True)
    verify_exp = options.get('verify_exp', True)
    
    # Split token
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise DecodeError("Invalid token format")
        
        header_b64, payload_b64, signature_b64 = parts
        
        # Decode header and payload
        header_json = _base64url_decode(header_b64.encode('utf-8'))
        payload_json = _base64url_decode(payload_b64.encode('utf-8'))
        
        header = json.loads(header_json.decode('utf-8'))
        payload = json.loads(payload_json.decode('utf-8'))
        
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:
        raise DecodeError(f"Invalid token: {str(e)}")
    
    # Check algorithm
    if verify_signature:
        if not algorithms:
            raise DecodeError("Algorithms must be specified for verification")
        
        if header.get('alg') not in algorithms:
            raise DecodeError(f"Algorithm {header.get('alg')} not allowed")
    
    # Verify signature
    if verify_signature:
        if header.get('alg') == "HS256":
            # Recreate signing input
            signing_input = (header_b64 + '.' + payload_b64).encode('utf-8')
            
            # Calculate expected signature
            key_bytes = _to_bytes(key)
            expected_signature = hmac.new(
                key_bytes, 
                signing_input, 
                hashlib.sha256
            ).digest()
            
            # Get actual signature
            actual_signature = _base64url_decode(signature_b64.encode('utf-8'))
            
            # Compare signatures (use constant-time comparison)
            if not hmac.compare_digest(expected_signature, actual_signature):
                raise InvalidSignatureError("Signature verification failed")
        else:
            raise DecodeError(f"Algorithm {header.get('alg')} not supported")
    
    # Verify expiration
    if verify_exp and 'exp' in payload:
        current_time = time.time()
        exp_time = payload['exp']
        
        if not isinstance(exp_time, (int, float)):
            raise DecodeError("Invalid exp claim")
        
        # Apply leeway
        if current_time > exp_time + leeway:
            raise ExpiredSignatureError("Signature has expired")
    
    return payload