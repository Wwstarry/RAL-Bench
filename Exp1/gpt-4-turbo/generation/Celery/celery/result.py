import time

class AsyncResult:
    def __init__(self, task_id, backend):
        self.id = task_id
        self._backend = backend

    def get(self, timeout=None):
        waited = 0
        interval = 0.1
        while True:
            meta = self._backend.get_result(self.id)
            if meta and meta['status'] in ('SUCCESS', 'FAILURE'):
                if meta['status'] == 'SUCCESS':
                    return meta['result']
                else:
                    exc = meta['result']
                    raise exc if isinstance(exc, Exception) else Exception(str(exc))
            time.sleep(interval)
            waited += interval
            if timeout is not None and waited >= timeout:
                raise TimeoutError("Timeout waiting for result.")

    def successful(self):
        meta = self._backend.get_result(self.id)
        return meta and meta['status'] == 'SUCCESS'

    def failed(self):
        meta = self._backend.get_result(self.id)
        return meta and meta['status'] == 'FAILURE'