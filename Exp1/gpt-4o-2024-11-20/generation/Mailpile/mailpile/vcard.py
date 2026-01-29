import re

class VCardLine:
    """
    A class to parse and serialize individual lines of a vCard.
    """
    def __init__(self, key, value, params=None):
        self.key = key
        self.value = value
        self.params = params or {}

    @classmethod
    def parse(cls, line):
        """
        Parse a vCard line into its components.
        """
        parts = line.split(':', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid vCard line: {line}")
        key, value = parts
        params = {}
        if ';' in key:
            key, param_str = key.split(';', 1)
            for param in param_str.split(';'):
                if '=' in param:
                    k, v = param.split('=', 1)
                    params[k] = v
        return cls(key, value, params)

    def serialize(self):
        """
        Serialize the vCard line back to a string.
        """
        param_str = ''.join(f';{k}={v}' for k, v in self.params.items())
        return f"{self.key}{param_str}:{self.value}"