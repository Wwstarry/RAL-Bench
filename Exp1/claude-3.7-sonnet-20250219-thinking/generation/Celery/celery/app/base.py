import uuid
from celery.app.task import Task
from celery.backends import get_backend
from celery.utils import gen_task_name
from celery._state import set_current_app

class Celery:
    """Celery application instance."""
    
    def __init__(self, name=None, broker=None, backend=None, broker_url=None, result_backend=None, **kwargs):
        self.name = name or "celery"
        self.tasks = {}
        self.broker_url = broker_url or broker or "memory://"
        self.result_backend = result_backend or backend or "memory://"
        self.conf = Config(app=self)
        self.Task = self._get_task_cls()
        self._backend = get_backend(self.result_backend)
        set_current_app(self)
        
    def _get_task_cls(self):
        """Create a base Task class for this app."""
        return type("Task", (Task,), {"app": self})
        
    def task(self, *args, **options):
        """Decorator to create a task."""
        def _inner(func):
            task_name = options.get('name') or gen_task_name(self.name, func.__name__)
            task = self.Task(func, name=task_name, app=self, **options)
            self.tasks[task_name] = task
            return task
        
        if args and callable(args[0]):
            return _inner(args[0])
        return _inner
    
    def send_task(self, name, args=None, kwargs=None, **options):
        """Send a task by name."""
        args = args or []
        kwargs = kwargs or {}
        task = self.tasks.get(name)
        if task is None:
            # If the task is not registered, create a dynamic task
            task = self.Task(None, name=name, app=self)
            self.tasks[name] = task
        
        return task.apply_async(args=args, kwargs=kwargs, **options)
    
    def worker_main(self, argv=None):
        """Start a worker instance."""
        # Simplified worker startup
        return 0
        
    def finalize(self):
        """Clean up resources."""
        pass


class Config:
    """Configuration object for Celery app."""
    
    def __init__(self, app=None):
        self.app = app
        self.task_always_eager = False
        self.task_eager_propagates = False
        self.result_backend = "memory://"
        self.broker_url = "memory://"
        self.broker_connection_retry = True
        self.broker_connection_max_retries = 100
        self.broker_connection_timeout = 4.0
        self.result_expires = 24 * 60 * 60  # 1 day
        
    def update(self, obj=None, **kwargs):
        """Update configuration."""
        if obj:
            for key, value in obj.items() if hasattr(obj, 'items') else obj:
                setattr(self, key, value)
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self