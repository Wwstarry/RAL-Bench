import sys

_color_codes = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    None: None,
}


def _style_ansi(fg=None, bold=None, dim=None, reset=True):
    codes = []
    if bold:
        codes.append("1")
    if dim:
        codes.append("2")
    if fg in _color_codes and _color_codes[fg] is not None:
        codes.append(str(_color_codes[fg]))
    if not codes:
        return "", ""
    start = "\033[" + ";".join(codes) + "m"
    end = "\033[0m" if reset else ""
    return start, end


def echo(message=None, file=None, nl=True, err=False):
    if file is None:
        file = sys.stderr if err else sys.stdout
    if message is None:
        message = ""
    text = str(message)
    if nl:
        text += "\n"
    try:
        file.write(text)
    except Exception:
        # In case stream is bytes-like, encode utf-8
        try:
            file.buffer.write(text.encode("utf-8"))
        except Exception:
            pass
    try:
        file.flush()
    except Exception:
        pass


def secho(message=None, file=None, nl=True, err=False, fg=None, bold=None, dim=None, color=None, reset=True, **kwargs):
    # color=None means enable by default if a style is specified
    do_color = (color is None and (fg or bold or dim)) or (color is True)
    if do_color:
        start, end = _style_ansi(fg=fg, bold=bold, dim=dim, reset=reset)
        echo(f"{start}{message}{end}", file=file, nl=nl, err=err)
    else:
        echo(message, file=file, nl=nl, err=err)