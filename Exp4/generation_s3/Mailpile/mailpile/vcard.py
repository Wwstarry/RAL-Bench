from typing import Dict, List, Optional, Union


def vcard_escape(text: str) -> str:
    if text is None:
        text = ''
    if not isinstance(text, str):
        text = str(text)
    # Escape backslash first.
    text = text.replace('\\', '\\\\')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('\n', '\\n')
    text = text.replace(';', r'\;')
    text = text.replace(',', r'\,')
    return text


def vcard_unescape(text: str) -> str:
    if text is None:
        return ''
    if not isinstance(text, str):
        text = str(text)

    out = []
    i = 0
    L = len(text)
    while i < L:
        ch = text[i]
        if ch != '\\' or i + 1 >= L:
            out.append(ch)
            i += 1
            continue

        nxt = text[i + 1]
        if nxt in ('n', 'N'):
            out.append('\n')
            i += 2
        elif nxt in ('\\', ',', ';'):
            out.append(nxt)
            i += 2
        else:
            # Unknown escape: drop backslash, keep char (best-effort)
            out.append(nxt)
            i += 2

    return ''.join(out)


def _find_unescaped_colon(s: str) -> int:
    esc = False
    for i, ch in enumerate(s):
        if esc:
            esc = False
            continue
        if ch == '\\':
            esc = True
            continue
        if ch == ':':
            return i
    return -1


def _split_unescaped(s: str, sep: str) -> List[str]:
    out = []
    buf = []
    esc = False
    for ch in s:
        if esc:
            buf.append(ch)
            esc = False
            continue
        if ch == '\\':
            buf.append(ch)
            esc = True
            continue
        if ch == sep:
            out.append(''.join(buf))
            buf = []
        else:
            buf.append(ch)
    out.append(''.join(buf))
    return out


class VCardLine(object):
    def __init__(
        self,
        name: str = None,
        value: str = '',
        attrs: Optional[Dict[str, bool]] = None,
        params: Optional[Dict[str, List[str]]] = None,
        line: Optional[Union[str, bytes]] = None
    ):
        self.name = ''
        self.value = ''
        self.attrs: Dict[str, bool] = {}
        self.params: Dict[str, List[str]] = {}

        if line is not None:
            parsed = self.Parse(line)
            self.name = parsed.name
            self.value = parsed.value
            self.attrs = dict(parsed.attrs)
            self.params = {k: list(v) for k, v in parsed.params.items()}
        else:
            if name is not None:
                self.name = str(name).upper()
            self.value = '' if value is None else str(value)
            self.attrs = {} if attrs is None else dict(attrs)
            # Normalize keys to uppercase, values to lists of strings
            if params is None:
                self.params = {}
            else:
                p = {}
                for k, v in params.items():
                    ku = str(k).upper()
                    if v is None:
                        p[ku] = []
                    elif isinstance(v, (list, tuple)):
                        p[ku] = [str(x) for x in v]
                    else:
                        p[ku] = [str(v)]
                self.params = p

    @classmethod
    def Parse(cls, line: Union[str, bytes]) -> "VCardLine":
        if isinstance(line, (bytes, bytearray)):
            s = bytes(line).decode('utf-8', 'replace')
        else:
            s = str(line)

        s = s.strip('\r\n')
        cpos = _find_unescaped_colon(s)
        if cpos < 0:
            raise ValueError('Malformed vCard line (missing colon)')

        header = s[:cpos]
        value = s[cpos + 1:]

        parts = _split_unescaped(header, ';')
        if not parts or parts[0] == '':
            raise ValueError('Malformed vCard line (missing name)')

        name = parts[0].upper()
        attrs: Dict[str, bool] = {}
        params: Dict[str, List[str]] = {}

        for seg in parts[1:]:
            if seg == '':
                continue
            if '=' in seg:
                k, v = seg.split('=', 1)
                ku = k.strip().upper()
                # v may have comma-separated values, possibly escaped
                raw_vals = _split_unescaped(v, ',')
                vals = [vcard_unescape(rv) for rv in raw_vals if rv != '']
                params[ku] = vals
            else:
                attrs[seg.strip().upper()] = True

        obj = cls(name=name, value=vcard_unescape(value), attrs=attrs, params=params)
        return obj

    def as_vcardline(self) -> str:
        name = (self.name or '').upper()
        if not name:
            raise ValueError('VCardLine has no name')

        chunks = [name]

        # Emit params first (sorted) then attrs (sorted) for deterministic output.
        for pk in sorted(self.params.keys()):
            vals = self.params.get(pk) or []
            ev = ','.join(vcard_escape(v) for v in vals)
            chunks.append('%s=%s' % (pk.upper(), ev))
        for ak in sorted(self.attrs.keys()):
            if self.attrs.get(ak):
                chunks.append(ak.upper())

        return '%s:%s' % (';'.join(chunks), vcard_escape(self.value))

    def __str__(self) -> str:
        return self.as_vcardline()