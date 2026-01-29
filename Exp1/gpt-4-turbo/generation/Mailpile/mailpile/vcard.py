import re

class VCardLine:
    """
    Represents a single line in a vCard file.
    Handles parsing and serialization.
    """

    def __init__(self, name, params=None, value=''):
        self.name = name.upper()
        self.params = params or {}
        self.value = value

    @classmethod
    def parse(cls, line):
        """
        Parse a vCard line into name, params, value.
        Example: EMAIL;TYPE=INTERNET:foo@bar.com
        """
        # Split into name/params and value
        if ':' not in line:
            raise ValueError('Invalid vCard line: no ":" separator')
        head, value = line.split(':', 1)
        parts = head.split(';')
        name = parts[0]
        params = {}
        for param in parts[1:]:
            if '=' in param:
                k, v = param.split('=', 1)
                params[k.upper()] = v
            else:
                params[param.upper()] = None
        return cls(name, params, value)

    def serialize(self):
        """
        Serialize the VCardLine back to a string.
        """
        params = []
        for k, v in self.params.items():
            if v is not None:
                params.append('%s=%s' % (k, v))
            else:
                params.append(k)
        head = ';'.join([self.name] + params)
        return '%s:%s' % (head, self.value)

    def __str__(self):
        return self.serialize()