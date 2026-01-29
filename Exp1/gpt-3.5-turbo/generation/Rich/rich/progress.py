import time
import sys

class Task:
    def __init__(self, description, total=100):
        self.description = description
        self.total = total
        self.completed = 0
        self.finished = False

    def advance(self, amount=1):
        if not self.finished:
            self.completed += amount
            if self.completed >= self.total:
                self.completed = self.total
                self.finished = True

    @property
    def progress(self):
        if self.total == 0:
            return 1.0
        return min(self.completed / self.total, 1.0)

class Progress:
    def __init__(self, console=None, width=40):
        self.console = console
        self.tasks = []
        self.width = width

    def add_task(self, description, total=100):
        task = Task(description, total)
        self.tasks.append(task)
        return task

    def advance(self, task, amount=1):
        task.advance(amount)
        self.refresh()

    def refresh(self):
        # Clear previous lines
        if self.console is None:
            file = sys.stdout
        else:
            file = self.console.file
        # Move cursor up to overwrite previous progress bars
        for _ in self.tasks:
            file.write("\x1b[1A")  # cursor up
            file.write("\x1b[2K")  # clear line
        # Render progress bars
        for task in self.tasks:
            bar = self._render_bar(task)
            file.write(bar + "\n")
        file.flush()

    def _render_bar(self, task):
        bar_width = self.width
        completed_width = int(bar_width * task.progress)
        remaining_width = bar_width - completed_width
        bar = "[" + "#" * completed_width + "-" * remaining_width + "]"
        percent = int(task.progress * 100)
        return f"{task.description} {bar} {percent}%"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Clear progress bars on exit
        if self.console is None:
            file = sys.stdout
        else:
            file = self.console.file
        for _ in self.tasks:
            file.write("\x1b[1A")  # cursor up
            file.write("\x1b[2K")  # clear line
        file.flush()