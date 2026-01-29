import sys
import threading
import time
import traceback
import os
import inspect
from collections import deque

# Log levels similar to Loguru
LEVELS = {
    "TRACE": 5,
    "DEBUG": 10,
    "INFO": 20,
    "SUCCESS": 25,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

LEVEL_NAMES = {v: k for k, v in LEVELS.items()}

def _default_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def _format_exception(exc):
    if exc is None:
        return ""
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    return tb

def _repr(value):
    # Use str() for most, repr() for some types?
    # Loguru uses str() for message formatting generally.
    # For bound context, str() is used.
    try:
        return str(value)
    except Exception:
        return repr(value)

class Record:
    __slots__ = (
        "time",
        "level",
        "levelno",
        "message",
        "exception",
        "extra",
        "file",
        "line",
        "function",
        "thread",
        "thread_name",
        "process",
        "process_name",
        "elapsed",
        "record",
    )

    def __init__(self, logger, levelno, message, args, kwargs, exception, extra):
        self.time = _default_time()
        self.levelno = levelno
        self.level = LEVEL_NAMES.get(levelno, "LEVEL{}".format(levelno))
        self.message = message
        self.exception = exception
        self.extra = extra or {}
        self.file = None
        self.line = None
        self.function = None
        self.thread = threading.get_ident()
        self.thread_name = threading.current_thread().name
        self.process = os.getpid()
        self.process_name = None
        self.elapsed = None
        self.record = self

        # Format message with args and kwargs
        try:
            if args or kwargs:
                self.message = message.format(*args, **kwargs)
            else:
                self.message = str(message)
        except Exception:
            # fallback to str(message)
            self.message = str(message)

        # Get caller info (skip frames inside logger)
        frame = None
        try:
            frame = inspect.currentframe()
            # Walk up until we find a frame outside this module
            while frame:
                mod = frame.f_globals.get("__name__", "")
                if mod != __name__:
                    break
                frame = frame.f_back
            if frame is not None:
                self.file = frame.f_code.co_filename
                self.line = frame.f_lineno
                self.function = frame.f_code.co_name
        finally:
            del frame

class Sink:
    def __init__(self, sink, levelno, format_str, filter=None):
        self.sink = sink
        self.levelno = levelno
        self.format_str = format_str or "{time} | {level} | {message}"
        self.filter = filter
        self.enabled = True
        self.lock = threading.Lock()

    def write(self, record):
        if not self.enabled:
            return
        if record.levelno < self.levelno:
            return
        if self.filter is not None:
            try:
                if not self.filter(record):
                    return
            except Exception:
                # ignore filter exceptions
                return
        try:
            formatted = self.format(record)
        except Exception:
            formatted = record.message
        try:
            with self.lock:
                if callable(self.sink):
                    self.sink(formatted)
                else:
                    # file-like object
                    self.sink.write(formatted)
                    if hasattr(self.sink, "flush"):
                        self.sink.flush()
        except Exception:
            # ignore sink exceptions
            pass

    def format(self, record):
        # Support basic formatting with {time}, {level}, {message}, {exception}, {extra}
        # extra is a dict, we can expand keys as {extra[key]}
        # We'll support {extra[key]} and {extra} (stringified dict)
        # For simplicity, replace {extra} with string of extra dict
        # and {exception} with exception text if any
        out = self.format_str

        # Prepare a dict for format
        fmt_dict = {
            "time": record.time,
            "level": record.level,
            "message": record.message,
            "exception": _format_exception(record.exception),
            "file": record.file or "",
            "line": record.line or "",
            "function": record.function or "",
            "thread": record.thread,
            "thread_name": record.thread_name,
            "process": record.process,
            "process_name": record.process_name or "",
        }

        # Add extra keys flattened
        for k, v in record.extra.items():
            fmt_dict["extra." + k] = _repr(v)

        # Replace {extra} with stringified dict
        fmt_dict["extra"] = ", ".join(f"{k}={_repr(v)}" for k, v in record.extra.items())

        # Custom replacement for {extra[key]} patterns
        # We'll do a simple approach: replace {extra[key]} with value
        # This is a bit hacky but covers common usage
        import re
        def extra_key_repl(m):
            key = m.group(1)
            return fmt_dict.get("extra." + key, "")

        out = re.sub(r"\{extra\[([^\]]+)\]\}", extra_key_repl, out)

        try:
            out = out.format(**fmt_dict)
        except Exception:
            # fallback to message only
            out = record.message

        # Append exception if not included in format
        if "{exception}" not in self.format_str and record.exception is not None:
            out += "\n" + _format_exception(record.exception)

        # Ensure line ends with newline
        if not out.endswith("\n"):
            out += "\n"

        return out

class BoundLogger:
    def __init__(self, logger, bound_extra):
        self._logger = logger
        self._bound_extra = bound_extra or {}

    def _merge_extra(self, extra):
        merged = {}
        merged.update(self._bound_extra)
        if extra:
            merged.update(extra)
        return merged

    def add(self, sink, level="DEBUG", format=None, filter=None):
        return self._logger.add(sink, level=level, format=format, filter=filter)

    def remove(self, handler_id):
        return self._logger.remove(handler_id)

    def bind(self, **kwargs):
        new_extra = self._merge_extra(kwargs)
        return BoundLogger(self._logger, new_extra)

    def opt(self, exception=None, **kwargs):
        # opt returns a logger with options applied for one call
        # We'll implement exception and possibly other options
        return OptLogger(self, exception=exception, **kwargs)

    def _log(self, level, message, *args, exception=None, **kwargs):
        extra = self._merge_extra(kwargs.pop("extra", None))
        self._logger._log(level, message, *args, exception=exception, extra=extra, **kwargs)

    def debug(self, message, *args, exception=None, **kwargs):
        self._log("DEBUG", message, *args, exception=exception, **kwargs)

    def info(self, message, *args, exception=None, **kwargs):
        self._log("INFO", message, *args, exception=exception, **kwargs)

    def warning(self, message, *args, exception=None, **kwargs):
        self._log("WARNING", message, *args, exception=exception, **kwargs)

    def error(self, message, *args, exception=None, **kwargs):
        self._log("ERROR", message, *args, exception=exception, **kwargs)

class OptLogger:
    def __init__(self, bound_logger, exception=None, **kwargs):
        self._bound_logger = bound_logger
        self._exception = exception
        self._kwargs = kwargs

    def _log(self, level, message, *args, **kwargs):
        # Merge kwargs with self._kwargs
        merged_kwargs = {}
        merged_kwargs.update(self._kwargs)
        merged_kwargs.update(kwargs)
        self._bound_logger._log(level, message, *args, exception=self._exception, **merged_kwargs)

    def debug(self, message, *args, **kwargs):
        self._log("DEBUG", message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self._log("INFO", message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self._log("WARNING", message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self._log("ERROR", message, *args, **kwargs)

class Logger:
    def __init__(self):
        self._sinks = {}
        self._sink_id_seq = 0
        self._lock = threading.RLock()
        self._bound_extra = {}

        # Add default sink to stderr at level DEBUG
        self.add(sys.stderr, level="DEBUG")

    def add(self, sink, level="DEBUG", format=None, filter=None):
        """
        Add a sink to the logger.

        sink: callable or file-like object
        level: minimum level to log
        format: format string
        filter: callable(record) -> bool
        """
        with self._lock:
            levelno = self._level_to_no(level)
            sink_obj = Sink(sink, levelno, format, filter)
            self._sink_id_seq += 1
            handler_id = self._sink_id_seq
            self._sinks[handler_id] = sink_obj
            return handler_id

    def remove(self, handler_id):
        with self._lock:
            if handler_id in self._sinks:
                del self._sinks[handler_id]

    def _level_to_no(self, level):
        if isinstance(level, int):
            return level
        level = str(level).upper()
        return LEVELS.get(level, 10)

    def _log(self, level, message, *args, exception=None, extra=None, **kwargs):
        levelno = self._level_to_no(level)
        # Compose extra context from bound + passed extra
        merged_extra = {}
        merged_extra.update(self._bound_extra)
        if extra:
            merged_extra.update(extra)
        record = Record(self, levelno, message, args, kwargs, exception, merged_extra)
        with self._lock:
            sinks = list(self._sinks.values())
        for sink in sinks:
            sink.write(record)

    def bind(self, **kwargs):
        new_extra = {}
        new_extra.update(self._bound_extra)
        new_extra.update(kwargs)
        return BoundLogger(self, new_extra)

    def opt(self, exception=None, **kwargs):
        # Return OptLogger with options applied for one call
        bound_logger = BoundLogger(self, self._bound_extra)
        return OptLogger(bound_logger, exception=exception, **kwargs)

    def debug(self, message, *args, exception=None, **kwargs):
        self._log("DEBUG", message, *args, exception=exception, **kwargs)

    def info(self, message, *args, exception=None, **kwargs):
        self._log("INFO", message, *args, exception=exception, **kwargs)

    def warning(self, message, *args, exception=None, **kwargs):
        self._log("WARNING", message, *args, exception=exception, **kwargs)

    def error(self, message, *args, exception=None, **kwargs):
        self._log("ERROR", message, *args, exception=exception, **kwargs)