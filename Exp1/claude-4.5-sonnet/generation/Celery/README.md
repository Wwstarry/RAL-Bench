# Celery - Distributed Task Queue

This is a pure Python implementation of a distributed task queue library that is API-compatible with the core parts of Celery.

## Features

- Task registration via `@app.task` decorator
- Asynchronous task execution with `.delay()` and `.apply_async()`
- Result retrieval with `.get(timeout=...)`
- Task status checking with `.successful()` and `.failed()`
- In-memory broker and backend for testing
- Eager execution mode for synchronous testing
- Name-based task dispatch with `app.send_task()`

## Usage

```python
from celery import Celery

app = Celery('myapp', broker='memory://', backend='memory://')

@app.task
def add(x, y):
    return x + y

# Asynchronous execution
result = add.delay(4, 4)
print(result.get(timeout=1))  # 8

# Eager mode for testing
app.conf.task_always_eager = True
result = add.delay(2, 2)
print(result.get())  # 4
```

## Configuration

The application supports configuration via `app.conf`:

- `task_always_eager`: Execute tasks synchronously
- `task_eager_propagates`: Propagate exceptions in eager mode
- `broker_url`: Broker connection URL
- `result_backend`: Result backend URL

## Testing

The implementation supports in-memory broker and backend for testing without external dependencies:

```python
app = Celery('test', broker='memory://', backend='memory://')
app.conf.task_always_eager = True
```