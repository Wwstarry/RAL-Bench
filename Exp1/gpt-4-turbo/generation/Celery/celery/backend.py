class InMemoryBackend:
    def __init__(self, store=None):
        self._store = store if store is not None else {}

    def store_result(self, task_id, result, status, traceback=None):
        self._store[task_id] = {
            'result': result,
            'status': status,
            'traceback': traceback,
        }

    def get_result(self, task_id):
        return self._store.get(task_id)