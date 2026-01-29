class BaseObserver:
    """
    Base observer interface, providing the primary methods needed by the watchdog test suite.
    """

    def schedule(self, event_handler, path, recursive=False):
        """
        Schedules watching a path with the specified handler.
        """
        raise NotImplementedError

    def start(self):
        """
        Starts observing the scheduled paths.
        """
        raise NotImplementedError

    def stop(self):
        """
        Stops observing.
        """
        raise NotImplementedError

    def join(self, timeout=None):
        """
        Joins the observer thread, blocking until it finishes or the optional timeout expires.
        """
        raise NotImplementedError