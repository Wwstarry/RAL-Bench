class Request:
    """Request for executing a task."""
    
    def __init__(self, task_id, task, args, kwargs, **options):
        self.id = task_id
        self.task = task
        self.args = args
        self.kwargs = kwargs
        self.options = options
    
    def execute(self):
        """Execute the task."""
        return self.task(*self.args, **self.kwargs)