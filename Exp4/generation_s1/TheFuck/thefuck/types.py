from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Protocol, Sequence

from .utils import split_command


@dataclass(frozen=True)
class Command:
    script: str = ""
    command: str = ""
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    env: dict | None = None

    @property
    def parts(self) -> list[str]:
        return split_command(self.command)

    @property
    def name(self) -> str:
        parts = self.parts
        return parts[0] if parts else ""


class RuleFnMatch(Protocol):
    def __call__(self, command: Command) -> bool: ...


class RuleFnNew(Protocol):
    def __call__(self, command: Command) -> str | Sequence[str]: ...


@dataclass(frozen=True)
class Rule:
    name: str
    match: RuleFnMatch
    get_new_command: RuleFnNew
    priority: int = 1000
    enabled_by_default: bool = True

    def propose(self, command: Command) -> list[str]:
        res = self.get_new_command(command)
        if res is None:
            return []
        if isinstance(res, str):
            return [res]
        return [str(x) for x in res]


def ensure_rules(rules: Iterable[Rule]) -> list[Rule]:
    return list(rules)