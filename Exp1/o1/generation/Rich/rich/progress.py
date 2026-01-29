from .console import parse_color_markup, strip_color_markup
import time


class Task:
    """
    Represents a single progress task.
    """

    def __init__(self, task_id, description, total=None, completed=0, visible=True):
        self.id = task_id
        self.description = description
        self.total = total
        self.completed = completed
        self.visible = visible

    @property
    def finished(self):
        if self.total is not None:
            return self.completed >= self.total
        return False

    def progress_str(self):
        if self.total and self.total > 0:
            pct = (self.completed / self.total) * 100
            bar_size = 20
            filled = int((self.completed / self.total) * bar_size)
            bar = "#" * filled + "-" * (bar_size - filled)
            return f"[{bar}] {pct:.1f}%"
        else:
            return f"[{'#' * 20}]"

class Progress:
    """
    A minimal progress manager.
    """

    def __init__(self):
        self.tasks = []
        self.next_id = 1

    def add_task(self, description, total=None, start=True):
        task = Task(self.next_id, description, total=total, completed=0, visible=True)
        self.tasks.append(task)
        self.next_id += 1
        return task.id

    def update(self, task_id, advance=None, total=None, visible=None):
        for t in self.tasks:
            if t.id == task_id:
                if advance is not None:
                    t.completed += advance
                if total is not None:
                    t.total = total
                if visible is not None:
                    t.visible = visible
                # Bound t.completed by t.total if total is known
                if t.total is not None and t.completed > t.total:
                    t.completed = t.total

    def advance(self, task_id, steps=1):
        self.update(task_id, advance=steps)

    def __rich_console__(self, console):
        """
        Generate lines for the console. We'll show each visible task.
        """
        lines = []
        for t in self.tasks:
            if not t.visible:
                continue
            line = f"{t.id}. {t.description} {t.progress_str()}"
            lines.append(line)
        return lines