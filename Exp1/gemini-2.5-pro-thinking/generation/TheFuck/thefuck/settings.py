from .const import DEFAULT_SETTINGS

class Settings(dict):
    """A simple settings object that allows attribute-style access."""
    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.update(DEFAULT_SETTINGS)

    def __getattr__(self, item):
        return self.get(item)

settings = Settings()