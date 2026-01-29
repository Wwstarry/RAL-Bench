import sys
import threading
import time
import traceback
import datetime
import inspect
import os

# Level definitions
_LEVELS = {
    "TRACE": 5,
    "DEBUG": 10,
    "INFO": 20,
    "SUCCESS": 25,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

_LEVEL_NAMES = {v: k for k, v in _LEVELS.items()}

def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def _format_exc(exc_info):
    return "".join(traceback.format_exception(*exc_info))

def _get_frame(depth=1):
    try:
        return inspect.stack()[depth]
    except Exception:
        return None

class _Sink:
    def __init__(self, sink, level, format, filter=None, catch=True, enabled=True, colorize=False):
        self.sink = sink
        self.level = level
        self.format = format
        self.filter = filter
        self.catch = catch
        self.enabled = enabled
        self.colorize = colorize
        self.lock = threading.Lock()

    def write(self, message):
        if not self.enabled:
            return
        with self.lock:
            if callable(self.sink):
                self.sink(message)
            elif hasattr(self.sink, "write"):
                self.sink.write(message)
                if hasattr(self.sink, "flush"):
                    self.sink.flush()
            elif isinstance(self.sink, str):
                with open(self.sink, "a", encoding="utf8") as f:
                    f.write(message)
            else:
                raise ValueError("Invalid sink type")

class _Logger:
    def __init__(self, sinks=None, context=None, depth=1, exception=None, lazy=False, record=False, raw=False, enqueue=False):
        self._sinks = sinks if sinks is not None else []
        self._context = context if context is not None else {}
        self._depth = depth
        self._exception = exception
        self._lazy = lazy
        self._record = record
        self._raw = raw
        self._enqueue = enqueue

    def add(self, sink, level="DEBUG", format="{time} | {level} | {message}\n", filter=None, catch=True, colorize=False, **kwargs):
        if isinstance(level, str):
            level = _LEVELS.get(level.upper(), 20)
        s = _Sink(sink, level, format, filter, catch, enabled=True, colorize=colorize)
        self._sinks.append(s)
        return id(s)

    def remove(self, handle):
        for i, s in enumerate(self._sinks):
            if id(s) == handle:
                del self._sinks[i]
                return

    def bind(self, **kwargs):
        context = self._context.copy()
        context.update(kwargs)
        return _Logger(self._sinks, context, self._depth, self._exception, self._lazy, self._record, self._raw, self._enqueue)

    def opt(self, *, exception=None, lazy=False, record=False, raw=False, depth=None, enqueue=False):
        return _Logger(
            self._sinks,
            self._context,
            depth if depth is not None else self._depth,
            exception,
            lazy,
            record,
            raw,
            enqueue,
        )

    def _log(self, level, message, args, kwargs, depth, exception, lazy, record, raw):
        if lazy and callable(message):
            msg = message()
        else:
            msg = message

        if args or kwargs:
            try:
                msg = msg.format(*args, **kwargs)
            except Exception:
                msg = msg

        exc_info = None
        if exception is True:
            exc_info = sys.exc_info()
            if exc_info[0] is None:
                exc_info = None
        elif exception:
            exc_info = exception

        frame = _get_frame(depth + 1)
        file = frame.filename if frame else ""
        line = frame.lineno if frame else 0
        func = frame.function if frame else ""
        thread = threading.current_thread()
        thread_name = thread.name
        thread_id = thread.ident

        record_dict = {
            "time": _now(),
            "level": _LEVEL_NAMES.get(level, str(level)),
            "message": msg,
            "file": file,
            "line": line,
            "function": func,
            "thread": thread_name,
            "thread_id": thread_id,
            "name": os.path.basename(file),
            "process": os.getpid(),
            "extra": self._context,
        }

        if exc_info:
            record_dict["exception"] = _format_exc(exc_info)
        else:
            record_dict["exception"] = ""

        for sink in self._sinks:
            if not sink.enabled:
                continue
            if level < sink.level:
                continue
            if sink.filter and not sink.filter(record_dict):
                continue
            try:
                fmt = sink.format
                out = fmt
                for k, v in record_dict.items():
                    if k == "extra":
                        for ek, ev in v.items():
                            out = out.replace("{%s}" % ek, str(ev))
                    else:
                        out = out.replace("{%s}" % k, str(v))
                if exc_info and "{exception}" not in fmt:
                    out += record_dict["exception"]
                if not out.endswith("\n"):
                    out += "\n"
                sink.write(out if not raw else msg)
            except Exception:
                if sink.catch:
                    pass
                else:
                    raise

    def _make_log_method(self, level):
        def log_method(message, *args, **kwargs):
            self._log(
                level,
                message,
                args,
                kwargs,
                self._depth,
                self._exception,
                self._lazy,
                self._record,
                self._raw,
            )
        return log_method

    def catch(self, func=None, **kwargs):
        # Not fully implemented, stub for compatibility
        def decorator(f):
            def wrapper(*args, **kw):
                try:
                    return f(*args, **kw)
                except Exception:
                    self.error("Exception caught", exception=True)
                    raise
            return wrapper
        if func is None:
            return decorator
        else:
            return decorator(func)

    debug = property(lambda self: self._make_log_method(_LEVELS["DEBUG"]))
    info = property(lambda self: self._make_log_method(_LEVELS["INFO"]))
    warning = property(lambda self: self._make_log_method(_LEVELS["WARNING"]))
    error = property(lambda self: self._make_log_method(_LEVELS["ERROR"]))
    critical = property(lambda self: self._make_log_method(_LEVELS["CRITICAL"]))
    trace = property(lambda self: self._make_log_method(_LEVELS["TRACE"]))
    success = property(lambda self: self._make_log_method(_LEVELS["SUCCESS"]))

    def enable(self, handle):
        for s in self._sinks:
            if id(s) == handle:
                s.enabled = True

    def disable(self, handle):
        for s in self._sinks:
            if id(s) == handle:
                s.enabled = False

logger = _Logger()