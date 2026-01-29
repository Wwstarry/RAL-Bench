from .console import Text, Segment

class Task:
    def __init__(self, task_id, description, total, visible=True):
        self.id = task_id
        self.description = description
        self.total = total
        self.completed = 0
        self.visible = visible

class Progress:
    def __init__(self, *columns):
        self.tasks = []
        self._task_id_counter = 0
        # columns are ignored for this basic implementation

    def add_task(self, description, total=100.0, **kwargs):
        task = Task(self._task_id_counter, description, total, **kwargs)
        self.tasks.append(task)
        self._task_id_counter += 1
        return task.id

    def update(self, task_id, advance=None, completed=None, **kwargs):
        task = self.tasks[task_id]
        if advance is not None:
            task.completed += advance
        if completed is not None:
            task.completed = completed
        if task.total is not None:
            task.completed = min(task.completed, task.total)

    def track(self, sequence, description="Working...", total=None):
        if total is None:
            try:
                total = len(sequence)
            except (TypeError, AttributeError):
                total = 100.0
        
        task_id = self.add_task(description, total=total)
        for item in sequence:
            yield item
            self.update(task_id, advance=1)

    def __rich_console__(self, console, options):
        width = options.width
        for task in self.tasks:
            if not task.visible:
                continue
            
            percent_complete = 0.0
            if task.total:
                percent_complete = max(0.0, min(100.0, (task.completed / task.total) * 100))
            
            desc_text = task.description.ljust(20)
            percent_text = f"{percent_complete:3.1f}%"
            
            bar_width = width - len(desc_text) - 1 - 8 # 8 for percentage and brackets
            bar_width = max(5, bar_width)
            
            completed_len = int(bar_width * percent_complete / 100)
            remaining_len = bar_width - completed_len
            
            bar = "█" * completed_len + " " * remaining_len
            
            line = f"{desc_text} [{bar}] {percent_text}"
            yield Segment(line)