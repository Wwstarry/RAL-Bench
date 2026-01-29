# Celery Minimal

A minimal Celery-compatible distributed task queue library for testing.

## Features

- API compatible with core Celery interfaces
- In-memory broker for testing (`memory://`)
- Eager execution mode
- AsyncResult with timeout support
- Task decorator with bind option

## Usage

```python
from celery import Celery

app = Celery("tasks", broker_url="memory://")

@app.task
def add(x, y):
    return x + y

result = add.delay(4, 4)
print(result.get())  # 8
```

## Configuration

Set `task_always_eager=True` for immediate execution:

```python
app.conf.task_always_eager = True
```

## Testing

This library is designed to be API-compatible with Celery for testing purposes.