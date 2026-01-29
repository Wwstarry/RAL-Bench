import re


class VCardLine:
    """
    Represents a single line in a vCard, with parsing and serialization.
    """

    def __init__(self, name, params=None, value=''):
        self.name = name.upper()
        self.params = params or {}
        self.value = value

    @classmethod
    def parse(cls, line):
        """
        Parse a vCard line into a VCardLine object.
        Example line:
        "FN;CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE:John Doe"
        """
        if not line:
            raise ValueError("Empty line")

        # Split name/params and value
        if ':' not in line:
            raise ValueError("Invalid vCard line, missing ':' separator")

        head, value = line.split(':', 1)
        parts = head.split(';')
        name = parts[0]
        params = {}

        for param in parts[1:]:
            if '=' in param:
                k, v = param.split('=', 1)
                params[k.upper()] = v
            else:
                # Parameter without value
                params[param.upper()] = None

        return cls(name, params, value)

    def serialize(self):
        """
        Serialize the VCardLine back to a string.
        """
        params_str = ''
        for k, v in self.params.items():
            if v is None:
                params_str += ';' + k
            else:
                params_str += ';{}={}'.format(k, v)
        return '{}{}:{}'.format(self.name, params_str, self.value)