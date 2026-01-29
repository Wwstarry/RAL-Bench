from typing import Any, Callable, List, Optional, Type, Union

class ParamType:
    """Base class for parameter types."""
    pass

class Option:
    """Class to define command-line options."""
    
    def __init__(
        self,
        default: Any = ...,
        name: Optional[Union[str, List[str]]] = None,
        help: Optional[str] = None,
        required: bool = False,
        type: Optional[Type] = None,
        show_default: bool = True,
    ):
        self.default = default
        self.name = name
        self.help = help
        self.required = required
        self.type = type
        self.show_default = show_default

class Argument:
    """Class to define command-line arguments."""
    
    def __init__(
        self,
        default: Any = ...,
        help: Optional[str] = None,
        required: bool = True,
        type: Optional[Type] = None,
    ):
        self.default = default
        self.help = help
        self.required = required
        self.type = type