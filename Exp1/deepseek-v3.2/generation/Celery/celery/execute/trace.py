"""
Task execution tracing.
"""


class TraceInfo:
    """Task trace information."""
    
    def __init__(self, task_id, task_name):
        self.task_id = task_id
        self.task_name = task_name
        self.state = None
        self.result = None
        self.exception = None
        self.traceback = None
        self.retries = 0