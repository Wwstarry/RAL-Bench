import json
import base64
import hmac
import hashlib
import time
from .exceptions import (
    DecodeError, InvalidSignatureError, ExpiredSignatureError
)

class PyJWT:
    def __init__(self, options=None):
        self.options = {
            'verify_signature': True,
            'verify_exp': True,
            'verify_nbf': False,
            'verify_iat': False,
            'verify_aud': False,
            'verify_iss': False,
        }
        if options:
            self.options.update(options)

    def encode(self, payload, key, algorithm='HS256', headers=None, json_encoder=None):
        # Prepare Header
        header = {'typ': 'JWT', 'alg': algorithm}
        if headers:
            header.update(headers)
        
        # Serialize Header and Payload
        # Use separators to match compact JSON representation (no spaces)
        header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
        payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        
        header_b64 = self._base64url_encode(header_json)
        payload_b64 = self._base64url_encode(payload_json)
        
        signing_input = f"{header_b64}.{payload_b64}".encode('ascii')
        
        # Sign
        if algorithm == 'HS256':
            if not key:
                raise ValueError("Key is required for HS256")
            
            key_bytes = key.encode('utf-8') if isinstance(key, str) else key
            signature = hmac.new(key_bytes, signing_input, hashlib.sha256).digest()
            signature_b64 = self._base64url_encode(signature)
        elif algorithm == 'none':
            signature_b64 = ""
        else:
            raise NotImplementedError(f"Algorithm {algorithm} not supported")
            
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def decode(self, jwt, key="", algorithms=None, options=None, leeway=0, **kwargs):
        # Merge options
        merged_options = self.options.copy()
        if options:
            merged_options.update(options)
        
        # Support legacy 'verify' argument
        if 'verify' in kwargs:
            merged_options['verify_signature'] = kwargs['verify']

        # Ensure jwt is bytes for splitting
        if isinstance(jwt, str):
            jwt_bytes = jwt.encode('utf-8')
        else:
            jwt_bytes = jwt
            
        # Split Token
        try:
            signing_input, crypto_segment = jwt_bytes.rsplit(b'.', 1)
            header_segment, payload_segment = signing_input.split(b'.', 1)
        except ValueError:
            raise DecodeError("Not enough segments")
            
        # Decode Header
        try:
            header_data = self._base64url_decode(header_segment)
            header = json.loads(header_data)
        except Exception as e:
            raise DecodeError(f"Invalid header string: {e}")
            
        if not isinstance(header, dict):
             raise DecodeError("Invalid header string: must be a json object")

        # Decode Payload
        try:
            payload_data = self._base64url_decode(payload_segment)
            payload = json.loads(payload_data)
        except Exception as e:
            raise DecodeError(f"Invalid payload string: {e}")

        # Verify Signature
        if merged_options.get('verify_signature'):
            if algorithms is None:
                raise DecodeError("It is required that you specify a value for the 'algorithms' argument when calling decode().")
            
            alg = header.get('alg')
            if alg not in algorithms:
                raise InvalidSignatureError("The specified alg value is not allowed")
            
            if alg == 'HS256':
                key_bytes = key.encode('utf-8') if isinstance(key, str) else key
                
                # Recalculate signature
                expected_sig = hmac.new(key_bytes, signing_input, hashlib.sha256).digest()
                received_sig = self._base64url_decode(crypto_segment)
                
                if not hmac.compare_digest(expected_sig, received_sig):
                    raise InvalidSignatureError("Signature verification failed")

        # Verify Claims
        self._validate_claims(payload, merged_options, leeway=leeway)
        
        return payload

    def _validate_claims(self, payload, options, leeway=0):
        # Expiration (exp)
        if options.get('verify_exp'):
            if isinstance(payload, dict) and 'exp' in payload:
                try:
                    exp_val = float(payload['exp'])
                except ValueError:
                    raise DecodeError("Expiration must be a float or integer")
                
                # Handle leeway (int, float, or timedelta)
                if hasattr(leeway, 'total_seconds'):
                    leeway_seconds = leeway.total_seconds()
                else:
                    leeway_seconds = float(leeway)
                
                if exp_val < (time.time() - leeway_seconds):
                    raise ExpiredSignatureError("Signature has expired")

    @staticmethod
    def _base64url_encode(input_bytes):
        return base64.urlsafe_b64encode(input_bytes).decode('ascii').rstrip('=')

    @staticmethod
    def _base64url_decode(input_bytes):
        if isinstance(input_bytes, str):
            input_bytes = input_bytes.encode('ascii')
        
        rem = len(input_bytes) % 4
        if rem > 0:
            input_bytes += b'=' * (4 - rem)
        
        return base64.urlsafe_b64decode(input_bytes)