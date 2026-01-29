from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

from .console import Console


@dataclass
class Task:
    id: int
    description: str
    total: Optional[float] = None
    completed: float = 0.0
    visible: bool = True
    start_time: Optional[float] = None
    finished_time: Optional[float] = None

    @property
    def finished(self) -> bool:
        return self.total is not None and self.completed >= self.total

    @property
    def percentage(self) -> Optional[float]:
        if self.total in (None, 0):
            return None
        return max(0.0, min(100.0, (self.completed / self.total) * 100.0))


class Progress:
    """
    Minimal Progress compatible with a subset of rich.progress.Progress.

    Deterministic output: refresh() prints a single line per visible task.
    """
    def __init__(
        self,
        *columns: Any,
        console: Optional[Console] = None,
        auto_refresh: bool = False,
        refresh_per_second: float = 10,
        transient: bool = False,
        expand: bool = False,
    ) -> None:
        self.console = console or Console()
        self.auto_refresh = auto_refresh
        self.refresh_per_second = refresh_per_second
        self.transient = transient
        self.expand = expand
        self._tasks: Dict[int, Task] = {}
        self._task_order: List[int] = []
        self._next_id = 0
        self._started = False

    def __enter__(self) -> "Progress":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        self._started = True

    def stop(self) -> None:
        if self.transient:
            return
        # final refresh for deterministic output
        self.refresh()
        self._started = False

    def add_task(self, description: str, total: Optional[float] = 100.0, completed: float = 0.0, visible: bool = True) -> int:
        tid = self._next_id
        self._next_id += 1
        task = Task(id=tid, description=description, total=total, completed=completed, visible=visible, start_time=time.time())
        self._tasks[tid] = task
        self._task_order.append(tid)
        return tid

    def remove_task(self, task_id: int) -> None:
        self._tasks.pop(task_id, None)
        if task_id in self._task_order:
            self._task_order.remove(task_id)

    def update(
        self,
        task_id: int,
        *,
        total: Optional[float] = None,
        completed: Optional[float] = None,
        advance: Optional[float] = None,
        visible: Optional[bool] = None,
        description: Optional[str] = None,
    ) -> None:
        task = self._tasks[task_id]
        if total is not None:
            task.total = total
        if completed is not None:
            task.completed = completed
        if advance is not None:
            task.completed += advance
        if visible is not None:
            task.visible = visible
        if description is not None:
            task.description = description
        if task.finished and task.finished_time is None:
            task.finished_time = time.time()

    def advance(self, task_id: int, advance: float = 1.0) -> None:
        self.update(task_id, advance=advance)

    def tasks(self) -> Sequence[Task]:
        return [self._tasks[tid] for tid in self._task_order if tid in self._tasks]

    def _bar(self, task: Task, width: int = 20) -> str:
        if task.total in (None, 0):
            return "?" * width
        ratio = max(0.0, min(1.0, task.completed / task.total))
        filled = int(round(ratio * width))
        return "█" * filled + " " * (width - filled)

    def refresh(self) -> None:
        for tid in self._task_order:
            task = self._tasks.get(tid)
            if not task or not task.visible:
                continue
            bar = self._bar(task, 20)
            if task.total is None:
                suffix = f"{task.completed:.0f}"
            else:
                pct = task.percentage or 0.0
                suffix = f"{pct:>3.0f}% {task.completed:.0f}/{task.total:.0f}"
            line = f"{task.description} [{bar}] {suffix}"
            self.console.print(line, markup=False, emoji=False, soft_wrap=True)

    def track(
        self,
        sequence: Iterable[Any],
        *,
        total: Optional[float] = None,
        task_description: str = "Working",
    ) -> Iterator[Any]:
        if total is None:
            try:
                total = float(len(sequence))  # type: ignore[arg-type]
            except Exception:
                total = None
        task_id = self.add_task(task_description, total=total)
        for item in sequence:
            yield item
            self.advance(task_id, 1)
            # deterministic: do not auto-refresh unless explicitly used
        # mark completion
        if total is not None:
            self.update(task_id, completed=total)
        return