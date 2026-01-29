class ClickException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def show(self, file=None):
        from .utils import echo
        if file is None:
            from .utils import get_text_stderr
            file = get_text_stderr()
        echo('Error: %s' % self.message, file=file)

class UsageError(ClickException):
    def __init__(self, message, ctx=None):
        super().__init__(message)
        self.ctx = ctx

    def show(self, file=None):
        from .utils import echo
        if file is None:
            from .utils import get_text_stderr
            file = get_text_stderr()
        if self.ctx is not None:
            echo(self.ctx.get_usage() + '\n', file=file)
        echo('Error: %s' % self.message, file=file)

class BadParameter(UsageError):
    def __init__(self, message, ctx=None, param=None, param_hint=None):
        super().__init__(message, ctx)
        self.param = param
        self.param_hint = param_hint

class MissingParameter(BadParameter):
    pass

class Abort(RuntimeError):
    pass

class Exit(RuntimeError):
    def __init__(self, code=0):
        self.exit_code = code