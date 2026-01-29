import io

def read_until_whitespace(stream, maxchars=None):
    txt = b""
    while True:
        c = stream.read(1)
        if not c:
            break
        if c in b" \t\n\r\f\x00":
            stream.seek(-1, 1)
            break
        txt += c
        if maxchars and len(txt) >= maxchars:
            break
    return txt

def read_non_whitespace(stream):
    while True:
        c = stream.read(1)
        if not c:
            return b""
        if c not in b" \t\n\r\f\x00":
            stream.seek(-1, 1)
            break
    return stream.read(1)

def skip_whitespace(stream):
    while True:
        c = stream.read(1)
        if not c:
            break
        if c not in b" \t\n\r\f\x00":
            stream.seek(-1, 1)
            break