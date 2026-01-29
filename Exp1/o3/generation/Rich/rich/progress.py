"""
A tiny *rich.progress* re-implementation.

The full live-updating behaviour of Rich is **not** reproduced.  Instead, the
module focusses on deterministic textual output that can be captured by unit
tests.
"""

from __future__ import annotations

import itertools
import sys
from typing import Dict, Iterable, List, Iterator

from .console import Console


_BAR_WIDTH = 20


# --------------------------------------------------------------------------- #
# Task                                                                        #
# --------------------------------------------------------------------------- #


class Task:
    """
    Representation of one progress task.
    """

    def __init__(self, task_id: int, description: str, total: int | None) -> None:
        self.id: int = task_id
        self.description: str = description
        self.total: int | None = total
        self.completed: int = 0

    # support attribute style used by real Rich e.g. task.completed
    @property
    def remaining(self) -> int | None:
        return None if self.total is None else max(self.total - self.completed, 0)

    # debug-friendly representation
    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Task #{self.id} {self.completed}/{self.total} "
            f"'{self.description}'>"
        )


# --------------------------------------------------------------------------- #
# Progress                                                                    #
# --------------------------------------------------------------------------- #


class Progress:
    """
    Very minimal replacement for :class:`rich.progress.Progress`.

    Live updates are not supported – instead each call to *update* prints the
    current state on its own line.
    """

    _task_counter = itertools.count(1)

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self._tasks: Dict[int, Task] = {}

    # Context-manager helpers --------------------------------------------- #

    def __enter__(self) -> "Progress":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        """
        Print final state of all tasks when the *with* block ends.
        """
        for tid in sorted(self._tasks):
            self._render_task(self._tasks[tid])

    # Public API ----------------------------------------------------------- #

    def add_task(
        self,
        description: str,
        *,
        total: int | None = None,
        completed: int = 0,
    ) -> int:
        task_id = next(self._task_counter)
        task = Task(task_id, description, total)
        task.completed = completed
        self._tasks[task_id] = task
        self._render_task(task)
        return task_id

    def update(
        self,
        task_id: int,
        *,
        advance: int = 0,
        completed: int | None = None,
    ) -> None:
        task = self._tasks[task_id]
        if completed is not None:
            task.completed = completed
        else:
            task.completed += advance
        self._render_task(task)

    # helper --------------------------------------------------------------- #

    def _render_task(self, task: Task) -> None:
        """
        Render a single progress bar line for *task*.
        """
        total = task.total
        completed = task.completed
        if total in (None, 0):
            percentage = 100
            bar = "●" * _BAR_WIDTH
            progress_text = f"{completed}"
        else:
            percentage = min(int((completed / total) * 100), 100)
            filled = int((_BAR_WIDTH * completed) / total)
            bar = "█" * filled + "░" * (_BAR_WIDTH - filled)
            progress_text = f"{completed}/{total}"

        line = f"{task.description} [{bar}] {percentage:3d}% {progress_text}"
        # The real Rich overwrites the current line by using \r.  That makes
        # testing harder, so we simply print each update on its own line.
        self.console.print(line, markup=False, wrap=False, emoji=False, end="\n")

    # --------------------------------------------------------------------- #
    # Convenience track() helper – matches real Rich signature              #
    # --------------------------------------------------------------------- #

    def track(
        self,
        sequence: Iterable,
        description: str = "Working...",
        total: int | None = None,
    ) -> Iterator:
        """
        Iterator helper that automatically creates a task and updates it on
        every iteration, similar to :func:`rich.progress.track`.
        """
        if total is None:
            try:
                total = len(sequence)  # type: ignore[arg-type]
            except Exception:
                total = None
        task_id = self.add_task(description, total=total)
        for item in sequence:
            yield item
            self.update(task_id, advance=1)
        return  # pragma: no cover – implicit StopIteration

    # alias used by the context-manager track utility below
    def __iter__(self):  # pragma: no cover
        raise TypeError(
            "Progress itself is not iterable.  Use Progress.track(...) "
            "or rich.progress.track(...) to iterate over a sequence."
        )


# --------------------------------------------------------------------------- #
# Functional shorthand – mirrors real Rich                                   #
# --------------------------------------------------------------------------- #


def track(
    sequence: Iterable,
    description: str = "Working...",
    total: int | None = None,
    console: Console | None = None,
) -> Iterator:
    """
    Convenience wrapper around :class:`Progress` so that user code can write::

        for item in rich.progress.track(range(100)):
            ...

    and not care about explicit *Progress* management.
    """
    progress = Progress(console=console)
    with progress:
        yield from progress.track(sequence, description=description, total=total)


__all__ = ["Progress", "Task", "track"]