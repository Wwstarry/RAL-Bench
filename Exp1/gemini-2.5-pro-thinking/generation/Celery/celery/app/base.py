from ..backends.inmemory import InMemoryBackend
from .task import Task
from ..result import AsyncResult

class Celery:
    def __init__(self, main=None, broker=None, backend=None, **kwargs):
        self.main = main
        self._tasks = {}
        self.conf = self._setup_defaults()

        # Update conf from constructor arguments
        if broker:
            self.conf['broker_url'] = broker
        if backend:
            self.conf['result_backend'] = backend
        
        # Celery allows overriding config via kwargs
        self.conf.update(kwargs)

        self._configure_backend()

    def _setup_defaults(self):
        return {
            'task_always_eager': False,
            'broker_url': None,
            'result_backend': None,
        }

    def config_from_object(self, obj):
        """Load configuration from an object (e.g., a module or class)."""
        for key in dir(obj):
            if key.isupper():
                self.conf[key.lower()] = getattr(obj, key)
        
        # Re-configure with new settings
        self._configure_backend()

    def _configure_backend(self):
        """Initializes the result backend based on configuration."""
        backend_url = self.conf.get('result_backend')
        # This implementation only supports an in-memory backend to run without
        # external services. It is used by default or if 'memory' is in the URL.
        self.backend = InMemoryBackend(url=backend_url)
        # The broker is not implemented, as we rely on eager/local execution.

    def task(self, *args, **opts):
        """Decorator to create a new task."""
        def decorator(func):
            base = opts.pop('base', Task)
            name = opts.get('name') or self.gen_task_name(func.__name__, func.__module__)
            task_instance = base(func, self, name=name, **opts)
            self._tasks[name] = task_instance
            return task_instance

        if len(args) == 1 and callable(args[0]):
            # Usage: @app.task
            return decorator(args[0])
        # Usage: @app.task(name='foo')
        return decorator

    def gen_task_name(self, name, module):
        """Generate a task name from the function name and module."""
        if module:
            return f"{module}.{name}"
        return name

    def send_task(self, name, args=None, kwargs=None, **options):
        """Send a task by name."""
        if name not in self._tasks:
            raise KeyError(f"Task '{name}' not registered.")
        task = self._tasks[name]
        return task.apply_async(args=args, kwargs=kwargs, **options)

    @property
    def tasks(self):
        """The registry of tasks."""
        return self._tasks