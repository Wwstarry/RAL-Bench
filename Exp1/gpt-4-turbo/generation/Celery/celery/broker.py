import threading
import queue

class InMemoryBroker:
    def __init__(self):
        self._queue = queue.Queue()

    def put_message(self, message):
        self._queue.put(message)

    def get_message(self):
        try:
            return self._queue.get(block=False)
        except queue.Empty:
            return None