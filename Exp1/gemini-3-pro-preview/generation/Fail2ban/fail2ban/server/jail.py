from .filter import Filter

class Jail(object):
    """
    Jail object managing filter+actions coordination.
    """
    def __init__(self, name):
        self._name = name
        self._filter = Filter(self)
        self._actions = []
        self._enabled = False

    @property
    def name(self):
        return self._name

    @property
    def filter(self):
        return self._filter

    def addAction(self, action):
        self._actions.append(action)

    def start(self):
        self._enabled = True

    def stop(self):
        self._enabled = False

    def is_alive(self):
        return self._enabled