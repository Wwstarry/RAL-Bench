class Config:
    broker_url = 'memory://'
    result_backend = 'memory://'
    task_always_eager = False

    def __init__(self):
        self._data = {}

    def __getattr__(self, k):
        if k in self._data:
            return self._data[k]
        if hasattr(type(self), k):
            return getattr(type(self), k)
        raise AttributeError(k)

    def __setattr__(self, k, v):
        if k in ('_data',):
            object.__setattr__(self, k, v)
        else:
            self._data[k] = v

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        setattr(self, k, v)

    def update(self, d):
        for k, v in d.items():
            setattr(self, k, v)