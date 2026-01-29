import base64
import hashlib
import hmac
import json
import time

from .exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidSignatureError,
)

class PyJWT:
    def __init__(self):
        self.algorithms = {
            "HS256": self._sign_hs256,
        }

    def encode(self, payload, key, algorithm="HS256", **kwargs):
        if algorithm not in self.algorithms:
            raise ValueError(f"Algorithm {algorithm} is not supported")

        header = {
            "typ": "JWT",
            "alg": algorithm,
        }

        # Create encoded segments
        header_encoded = self._base64url_encode(json.dumps(header, separators=(",", ":")).encode())
        payload_encoded = self._base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
        
        # Create signing input
        signing_input = f"{header_encoded}.{payload_encoded}".encode()
        
        # Create signature
        signature_func = self.algorithms[algorithm]
        signature = signature_func(signing_input, key)
        
        # Return JWT
        return f"{header_encoded}.{payload_encoded}.{signature}"

    def decode(self, token, key, algorithms=["HS256"], options=None, leeway=0, **kwargs):
        if options is None:
            options = {}
        
        if not algorithms:
            raise DecodeError("No algorithms specified")

        # Parse token
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise DecodeError("Invalid token structure")
            
            header_encoded, payload_encoded, signature_encoded = parts
            
            # Decode header
            header_json = self._base64url_decode(header_encoded)
            header = json.loads(header_json)
            
            # Check algorithm
            alg = header.get("alg")
            if alg not in algorithms:
                raise DecodeError(f"Algorithm {alg} not allowed")
            
            if alg not in self.algorithms:
                raise DecodeError(f"Algorithm {alg} is not supported")
            
            # Verify signature
            signing_input = f"{header_encoded}.{payload_encoded}".encode()
            signature_func = self.algorithms[alg]
            expected_signature = signature_func(signing_input, key)
            
            if not self._safe_compare(signature_encoded, expected_signature):
                raise InvalidSignatureError("Signature verification failed")
            
            # Decode payload
            payload_json = self._base64url_decode(payload_encoded)
            payload = json.loads(payload_json)
            
            # Verify expiration if required
            verify_exp = options.get("verify_exp", True)
            if verify_exp:
                self._verify_exp(payload, leeway)
            
            return payload
            
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:
            raise DecodeError(f"Invalid token: {str(e)}") from e

    def _sign_hs256(self, msg, key):
        if isinstance(key, str):
            key = key.encode()
        signature = hmac.new(key, msg, hashlib.sha256).digest()
        return self._base64url_encode(signature)

    def _base64url_encode(self, data):
        return base64.urlsafe_b64encode(data).decode().rstrip("=")

    def _base64url_decode(self, data):
        padding = 4 - (len(data) % 4)
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data).decode()

    def _safe_compare(self, a, b):
        """Constant-time comparison to prevent timing attacks"""
        if len(a) != len(b):
            return False
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        return result == 0

    def _verify_exp(self, payload, leeway):
        exp = payload.get("exp")
        if exp is None:
            return
        
        current_time = time.time()
        if current_time > (exp + leeway):
            raise ExpiredSignatureError("Token has expired")