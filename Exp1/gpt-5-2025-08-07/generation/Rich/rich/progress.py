from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generator, Iterable, List, Optional


@dataclass
class Task:
    task_id: int
    description: str
    total: Optional[float]
    completed: float = 0.0
    visible: bool = True

    @property
    def remaining(self) -> Optional[float]:
        if self.total is None:
            return None
        return max(0.0, self.total - self.completed)

    @property
    def finished(self) -> bool:
        if self.total is None:
            return False
        return self.completed >= self.total


class Progress:
    def __init__(self, transient: bool = False, expand: bool = False) -> None:
        self.tasks: List[Task] = []
        self._next_id = 1
        self.transient = transient
        self.expand = expand

    def __enter__(self) -> "Progress":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # No live rendering cleanup required
        pass

    def add_task(self, description: str = "", total: Optional[float] = None, start: bool = True) -> int:
        t = Task(task_id=self._next_id, description=description, total=total, completed=0.0 if start else 0.0)
        self._next_id += 1
        self.tasks.append(t)
        return t.task_id

    def update(
        self,
        task_id: int,
        *,
        advance: Optional[float] = None,
        completed: Optional[float] = None,
        total: Optional[float] = None,
        description: Optional[str] = None,
        visible: Optional[bool] = None,
    ) -> None:
        t = self._get_task(task_id)
        if advance is not None:
            t.completed += float(advance)
        if completed is not None:
            t.completed = float(completed)
        if total is not None:
            t.total = float(total)
        if description is not None:
            t.description = description
        if visible is not None:
            t.visible = bool(visible)

    def advance(self, task_id: int, advance: float = 1.0) -> None:
        self.update(task_id, advance=advance)

    def _get_task(self, task_id: int) -> Task:
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        raise KeyError(f"No such task {task_id}")

    def render(self, width: int = 80) -> str:
        lines: List[str] = []
        # Pick a reasonable bar width
        for t in self.tasks:
            if not t.visible:
                continue
            desc = t.description or ""
            desc = desc.strip()
            # Reserve space for " xx% x/y"
            counters = ""
            if t.total is not None and t.total > 0:
                ratio = max(0.0, min(1.0, t.completed / t.total))
                percent = int(ratio * 100)
                completed_int = int(t.completed)
                total_int = int(t.total)
                counters = f" {completed_int}/{total_int} {percent:3d}%"
                bar_space = max(10, width - len(desc) - len(counters) - 5)
                filled = int(ratio * bar_space)
            else:
                percent = 0
                counters = ""
                bar_space = max(10, width - len(desc) - 5)
                filled = int((t.completed % 1.0) * bar_space)

            if len(desc) > max(0, width - (bar_space + len(counters) + 5)):
                desc = desc[: max(0, width - (bar_space + len(counters) + 5))]
            bar = "█" * filled + " " * (bar_space - filled)
            line = f"{desc} |{bar}|{counters}"
            lines.append(line)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render(80)


def track(
    sequence: Iterable[Any],
    description: str = "",
    total: Optional[int] = None,
) -> Generator[Any, None, None]:
    """
    Simple progress tracker: yields items from sequence and updates a single task internally.
    It does not live-render; intended for deterministic testing.
    """
    if total is None:
        try:
            total = len(sequence)  # type: ignore
        except Exception:
            total = None
    with Progress() as progress:
        task_id = progress.add_task(description=description, total=total)
        for item in sequence:
            yield item
            progress.advance(task_id, 1.0)
        # Final snapshot (not printed automatically; users may print(progress))
        # No automatic I/O here to keep deterministic behavior