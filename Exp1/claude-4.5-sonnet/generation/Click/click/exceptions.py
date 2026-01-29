"""
Click exceptions.
"""


class ClickException(Exception):
    """Base exception for all Click exceptions."""
    
    exit_code = 1
    
    def __init__(self, message):
        super().__init__(message)
        self.message = message
    
    def format_message(self):
        return self.message
    
    def show(self, file=None):
        from .termui import echo
        echo(f"Error: {self.format_message()}", err=True, file=file)


class UsageError(ClickException):
    """An error in command usage."""
    
    def __init__(self, message, ctx=None):
        super().__init__(message)
        self.ctx = ctx
    
    def show(self, file=None):
        from .termui import echo
        if self.ctx is not None:
            echo(self.ctx.get_usage(), err=True, file=file)
        echo(f"Error: {self.format_message()}", err=True, file=file)


class BadParameter(UsageError):
    """An error with a parameter."""
    
    def __init__(self, message, ctx=None, param=None):
        super().__init__(message, ctx)
        self.param = param


class Abort(RuntimeError):
    """An abort exception."""
    pass