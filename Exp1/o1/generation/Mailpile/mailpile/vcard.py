class VCardLine:
    """
    Represents a single VCard line with key, value, and optional parameters.
    """

    def __init__(self, key, value, params=None):
        self.key = key
        self.value = value
        self.params = params or {}

    def serialize(self):
        """
        Serialize the line back to VCard format:
        KEY;PARAMS:VALUE
        """
        parts = [self.key]
        for pk, pv in self.params.items():
            parts.append('%s=%s' % (pk.upper(), pv))
        return ';'.join(parts) + ':' + self.value

def parse_vcard_line(line):
    """
    Parse a single VCard line into (key, params, value).
    
    :param line: A raw VCard line
    :return: VCardLine instance
    """
    # Split into key/params vs value
    if ':' not in line:
        return VCardLine(key=line, value='')

    left, value = line.split(':', 1)
    parts = left.split(';')
    key = parts[0]
    params = {}
    for p in parts[1:]:
        if '=' in p:
            pk, pv = p.split('=', 1)
            params[pk.lower()] = pv
        else:
            params[p.lower()] = ''
    return VCardLine(key=key, value=value, params=params)