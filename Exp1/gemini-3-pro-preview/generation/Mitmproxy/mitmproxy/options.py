from typing import Optional, Sequence, Any

class Options(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._options = {}

    def add_option(
        self,
        name: str,
        typespec: type,
        default: Any,
        help: str,
        choices: Optional[Sequence[str]] = None,
    ) -> None:
        self[name] = default
        self._options[name] = {
            "typespec": typespec,
            "default": default,
            "help": help,
            "choices": choices,
        }

    def __getattr__(self, item):
        if item in self:
            return self[item]
        raise AttributeError(f"Option {item} not found")

    def __setattr__(self, key, value):
        if key == "_options":
            super().__setattr__(key, value)
        else:
            self[key] = value