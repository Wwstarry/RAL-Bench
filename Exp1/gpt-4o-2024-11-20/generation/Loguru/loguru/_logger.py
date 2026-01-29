import sys
import datetime
import threading


class Logger:
    def __init__(self):
        self._sinks = {}
        self._lock = threading.Lock()
        self._context = threading.local()
        self._context.vars = {}

    def add(self, sink, format="{time} | {level} | {message}", level="DEBUG"):
        with self._lock:
            sink_id = len(self._sinks) + 1
            self._sinks[sink_id] = {
                "sink": sink,
                "format": format,
                "level": level.upper(),
            }
            return sink_id

    def remove(self, sink_id):
        with self._lock:
            if sink_id in self._sinks:
                del self._sinks[sink_id]

    def bind(self, **kwargs):
        new_logger = Logger()
        new_logger._sinks = self._sinks
        new_logger._context.vars = {**self._context.vars, **kwargs}
        return new_logger

    def opt(self, **kwargs):
        return self.bind(**kwargs)

    def _log(self, level, message, **kwargs):
        record = {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message,
            **self._context.vars,
            **kwargs,
        }
        with self._lock:
            for sink_id, sink_info in self._sinks.items():
                if self._should_log(level, sink_info["level"]):
                    formatted_message = sink_info["format"].format(**record)
                    self._write_to_sink(sink_info["sink"], formatted_message)

    def _should_log(self, message_level, sink_level):
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        return levels.index(message_level) >= levels.index(sink_level)

    def _write_to_sink(self, sink, message):
        if callable(sink):
            sink(message)
        elif isinstance(sink, str):
            with open(sink, "a") as file:
                file.write(message + "\n")
        else:
            raise ValueError("Unsupported sink type")

    def debug(self, message, **kwargs):
        self._log("DEBUG", message, **kwargs)

    def info(self, message, **kwargs):
        self._log("INFO", message, **kwargs)

    def warning(self, message, **kwargs):
        self._log("WARNING", message, **kwargs)

    def error(self, message, **kwargs):
        self._log("ERROR", message, **kwargs)