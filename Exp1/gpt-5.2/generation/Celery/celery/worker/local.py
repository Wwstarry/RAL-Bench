from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


class InMemoryBackend:
    def __init__(self):
        self._lock = threading.Lock()
        self._data: Dict[str, Dict[str, Any]] = {}

    def store_result(self, task_id: str, result: Any, state: str = "SUCCESS", traceback: bool = False) -> None:
        with self._lock:
            self._data[task_id] = {"state": state, "result": result}

    def get_state(self, task_id: str) -> str:
        with self._lock:
            return self._data.get(task_id, {}).get("state", "PENDING")

    def get_result(self, task_id: str) -> Any:
        with self._lock:
            return self._data.get(task_id, {}).get("result", None)


@dataclass
class _Job:
    task: Any
    task_id: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    delay: float = 0.0


class LocalExecutor:
    """
    Executes tasks locally using threads; stores results in an in-memory backend.
    """

    def __init__(self, app: Any):
        self.app = app
        self.backend = InMemoryBackend()

    def submit(self, task: Any, task_id: str, args: Tuple[Any, ...], kwargs: Dict[str, Any], delay: float = 0.0) -> None:
        ignore = bool(getattr(self.app.conf, "task_ignore_result", False)) or bool(getattr(task, "ignore_result", False))
        self.backend.store_result(task_id, None, state="PENDING")

        job = _Job(task=task, task_id=task_id, args=args, kwargs=kwargs, delay=delay)

        t = threading.Thread(target=self._run, args=(job, ignore), daemon=True)
        t.start()

    def _run(self, job: _Job, ignore: bool) -> None:
        if job.delay and job.delay > 0:
            time.sleep(job.delay)

        request = {
            "id": job.task_id,
            "task": job.task.name,
            "args": job.args,
            "kwargs": job.kwargs,
            "retries": 0,
            "is_eager": False,
        }
        job.task._push_request(request)
        try:
            res = job.task.run(*job.args, **job.kwargs)
            if not ignore:
                self.backend.store_result(job.task_id, res, state="SUCCESS")
            else:
                # Even if ignored, mark success for readiness semantics
                self.backend.store_result(job.task_id, None, state="SUCCESS")
        except Exception as exc:
            if not ignore:
                self.backend.store_result(job.task_id, exc, state="FAILURE")
            else:
                self.backend.store_result(job.task_id, None, state="FAILURE")
        finally:
            job.task._pop_request()