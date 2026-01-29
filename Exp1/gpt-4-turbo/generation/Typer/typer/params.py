import inspect

class Option:
    def __init__(self, default=..., *, help=None, short=None, is_flag=False):
        self.default = default
        self.help = help
        self.short = short
        self.is_flag = is_flag

    def __repr__(self):
        return f"Option(default={self.default!r}, help={self.help!r}, short={self.short!r}, is_flag={self.is_flag!r})"

class Argument:
    def __init__(self, default=..., *, help=None):
        self.default = default
        self.help = help

    def __repr__(self):
        return f"Argument(default={self.default!r}, help={self.help!r})"