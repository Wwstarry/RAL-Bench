class BaseBackend:
    def __init__(self, app=None, url=None):
        self.app = app
        self.url = url

    def store_result(self, task_id, result, status, exception=None):
        raise NotImplementedError

    def get_meta(self, task_id):
        raise NotImplementedError