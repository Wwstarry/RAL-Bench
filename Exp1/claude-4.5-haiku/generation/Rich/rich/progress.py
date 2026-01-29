"""Progress bar rendering for the console."""

from typing import Optional, Iterable, TypeVar, Union, Any, List
from dataclasses import dataclass
import time

T = TypeVar("T")


@dataclass
class Task:
    """Represents a progress task."""

    id: int
    description: str
    total: Optional[float]
    completed: float = 0.0
    visible: bool = True
    start_time: Optional[float] = None
    stop_time: Optional[float] = None
    elapsed: float = 0.0

    def update(self, advance: float = 0.0, total: Optional[float] = None, refresh: bool = False) -> None:
        """Update the task progress."""
        if advance:
            self.completed += advance
        if total is not None:
            self.total = total

    def start(self) -> None:
        """Start the task."""
        if self.start_time is None:
            self.start_time = time.time()

    def stop(self) -> None:
        """Stop the task."""
        if self.stop_time is None:
            self.stop_time = time.time()

    def get_progress(self) -> float:
        """Get the progress as a fraction (0.0 to 1.0)."""
        if self.total is None or self.total == 0:
            return 0.0
        return min(1.0, self.completed / self.total)


class Progress:
    """A progress bar for tracking task progress."""

    def __init__(
        self,
        *columns: Any,
        console: Optional[Any] = None,
        auto_refresh: bool = True,
        refresh_per_second: float = 10.0,
        transient: bool = False,
        redirect_stdout: bool = True,
        redirect_stderr: bool = True,
        get_time: Optional[Any] = None,
        disable: bool = False,
        expand: bool = False,
    ):
        """Initialize a Progress instance."""
        self.columns = columns
        self.console = console
        self.auto_refresh = auto_refresh
        self.refresh_per_second = refresh_per_second
        self.transient = transient
        self.redirect_stdout = redirect_stdout
        self.redirect_stderr = redirect_stderr
        self.get_time = get_time or time.time
        self.disable = disable
        self.expand = expand

        self.tasks: List[Task] = []
        self._task_id_counter = 0
        self._started = False

    def add_task(
        self,
        description: str,
        start: bool = True,
        total: Optional[float] = None,
        completed: int = 0,
        visible: bool = True,
        refresh: bool = False,
    ) -> int:
        """Add a task to the progress bar."""
        task_id = self._task_id_counter
        self._task_id_counter += 1

        task = Task(
            id=task_id,
            description=description,
            total=total,
            completed=float(completed),
            visible=visible,
        )

        if start:
            task.start()

        self.tasks.append(task)
        return task_id

    def update(
        self,
        task_id: int,
        advance: float = 0.0,
        total: Optional[float] = None,
        completed: Optional[float] = None,
        visible: Optional[bool] = None,
        refresh: bool = False,
        description: Optional[str] = None,
    ) -> None:
        """Update a task."""
        for task in self.tasks:
            if task.id == task_id:
                if advance:
                    task.completed += advance
                if total is not None:
                    task.total = total
                if completed is not None:
                    task.completed = completed
                if visible is not None:
                    task.visible = visible
                if description is not None:
                    task.description = description
                break

    def start_task(self, task_id: int) -> None:
        """Start a task."""
        for task in self.tasks:
            if task.id == task_id:
                task.start()
                break

    def stop_task(self, task_id: int) -> None:
        """Stop a task."""
        for task in self.tasks:
            if task.id == task_id:
                task.stop()
                break

    def __enter__(self) -> "Progress":
        """Enter context manager."""
        self._started = True
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self._started = False

    def __iter__(self) -> "Progress":
        """Iterate over progress."""
        return self

    def __next__(self) -> Any:
        """Get next item."""
        raise StopIteration

    def track(
        self,
        sequence: Iterable[T],
        total: Optional[float] = None,
        task_id: Optional[int] = None,
        description: str = "",
    ) -> Iterable[T]:
        """Track progress over an iterable."""
        if total is None:
            try:
                total = len(sequence)  # type: ignore
            except TypeError:
                total = None

        if task_id is None:
            task_id = self.add_task(description, total=total)

        for item in sequence:
            yield item
            self.update(task_id, advance=1)

    def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def render(self, console: Optional[Any] = None) -> str:
        """Render the progress bar."""
        lines = []
        for task in self.tasks:
            if not task.visible:
                continue

            progress = task.get_progress()
            bar_length = 30
            filled = int(bar_length * progress)
            bar = "█" * filled + "░" * (bar_length - filled)

            if task.total is not None:
                percentage = int(progress * 100)
                line = f"{task.description} [{bar}] {percentage}%"
            else:
                line = f"{task.description} [{bar}]"

            lines.append(line)

        return "\n".join(lines)