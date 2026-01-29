from typing import Any, Optional


class BaseParam:
    def __init__(
        self,
        default: Any = ...,
        help: Optional[str] = None,
    ):
        self.default = default
        self.help = help


class Argument(BaseParam):
    def __init__(
        self,
        default: Any = ...,
        help: Optional[str] = None,
    ):
        super().__init__(default=default, help=help)


class Option(BaseParam):
    def __init__(
        self,
        default: Any = ...,
        help: Optional[str] = None,
    ):
        super().__init__(default=default, help=help)


# For compatibility with tests
ArgumentInfo = Argument
OptionInfo = Option