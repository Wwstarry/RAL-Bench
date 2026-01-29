import sys
from typing import Any, NoReturn, Optional


def echo(
    message: Any = "",
    err: bool = False,
    nl: bool = True,
) -> None:
    file = sys.stderr if err else sys.stdout
    print(message, file=file, end="\n" if nl else "")


class Exit(Exception):
    def __init__(self, code: int = 0) -> None:
        self.exit_code = code
        super().__init__(f"Exit with code {code}")