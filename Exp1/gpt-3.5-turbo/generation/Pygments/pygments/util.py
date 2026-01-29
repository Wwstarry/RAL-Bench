import sys

def get_choice_opt(opt, choices, default=None):
    if opt is None:
        return default
    opt = opt.lower()
    if opt not in choices:
        raise ValueError(f"Invalid option '{opt}', expected one of {choices}")
    return opt

def shebang_matches(text, *interpreters):
    # Check if the first line is a shebang matching any of the given interpreters
    if not text:
        return False
    first_line = text.splitlines()[0]
    if not first_line.startswith('#!'):
        return False
    for interp in interpreters:
        if interp in first_line:
            return True
    return False

def guess_encoding(data):
    # Try to guess encoding from coding cookie (PEP263)
    import re
    coding_re = re.compile(br'coding[:=]\s*([-\w.]+)')
    lines = data.split(b'\n', 2)[:2]
    for line in lines:
        m = coding_re.search(line)
        if m:
            return m.group(1).decode('ascii')
    return 'utf-8'

def iteritems(d):
    # Python 2/3 compatibility for dict.items()
    return getattr(d, 'iteritems', d.items)()