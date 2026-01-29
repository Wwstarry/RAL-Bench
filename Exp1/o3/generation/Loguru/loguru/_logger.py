import sys
import inspect
import itertools
import datetime
import traceback
from threading import RLock


__all__ = ["Logger"]

# Simple numeric representation (compatible with stdlib)
_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
}

_LEVEL_NAMES = {v: k for k, v in _LEVELS.items()}


def _now():
    # ISO-like time with millisecond precision
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _format_extra(extra: dict) -> str:
    if not extra:
        return ""
    return " ".join(f"{k}={v}" for k, v in extra.items())


class _Sink:
    """Internal helper describing a registered sink."""

    _id_iter = itertools.count(1)

    def __init__(self, sink, level, fmt):
        self.id = next(_Sink._id_iter)

        # Resolve sink target -------------------------------------------------
        if isinstance(sink, str):
            # Consider *string* as a file path
            self._file = open(sink, "a", encoding="utf-8")
            self._func = None
            self._writer = self._file
        elif hasattr(sink, "write") and callable(sink.write):
            self._func = None
            self._writer = sink
            self._file = None
        elif callable(sink):
            # A function which receives the rendered message
            self._func = sink
            self._writer = None
            self._file = None
        elif sink is None:
            # default to stderr
            self._writer = sys.stderr
            self._func = None
            self._file = None
        else:
            raise ValueError("Unsupported sink type: %r" % (sink,))

        # Logging parameters --------------------------------------------------
        if isinstance(level, str):
            self.level_no = _LEVELS.get(level.upper(), 0)
        else:
            self.level_no = int(level)

        self.fmt = fmt or "{time} | {level} | {message} {extra}"

    def write(self, rendered: str):
        # choose output method
        if self._func:
            try:
                self._func(rendered)
            except Exception:
                # We don't want to crash the program because a sink failed.
                # Write error to stderr.
                sys.stderr.write("Loguru-like sink function raised:\n")
                traceback.print_exc(file=sys.stderr)
        else:
            try:
                self._writer.write(rendered + "\n")
                if hasattr(self._writer, "flush"):
                    self._writer.flush()
            except Exception:
                sys.stderr.write("Loguru-like sink write failed:\n")
                traceback.print_exc(file=sys.stderr)

    def close(self):
        if self._file:
            try:
                self._file.close()
            except Exception:
                pass


class _OptLogger:
    """Returned by .opt(). It stores options to be used on subsequent log call."""

    def __init__(self, parent, **opts):
        self._parent = parent
        self._opts = opts

    def __getattr__(self, item):
        if item in ("debug", "info", "warning", "error"):
            def _method(msg, *args, **kwargs):
                self._parent._log(
                    level_name=item.upper(),
                    message=msg,
                    args=args,
                    kwargs=kwargs,
                    extra=self._parent._extra,
                    opts=self._opts,
                )
            return _method
        raise AttributeError(item)


class Logger:
    """
    A very small subset of Loguru's logger focused on the API needed for tests.
    Feel free to instantiate several loggers, but library also provides a
    pre-instantiated 'logger' object.
    """

    def __init__(self, sinks=None, extra=None, _lock=None):
        self._sinks = sinks[:] if sinks else []
        self._extra = dict(extra) if extra else {}
        self._lock = _lock or RLock()

    # --------------------------------------------------------------------- #
    # Sink management                                                       #
    # --------------------------------------------------------------------- #
    def add(self, sink=None, level="DEBUG", format="{time} | {level} | {message} {extra}"):
        """
        Register a new sink. 'sink' can be:
          • a callable accepting one argument (the rendered string),
          • a file-like object with a .write() method,
          • a file path as string,
          • None / omitted => sys.stderr is used.

        Returns an integer id used to remove the sink later.
        """
        s = _Sink(sink or sys.stderr, level, format)
        with self._lock:
            self._sinks.append(s)
        return s.id

    def remove(self, sink_id=None):
        """
        Remove a sink by id. If sink_id is None, remove all sinks.
        """
        with self._lock:
            if sink_id is None:
                while self._sinks:
                    self._sinks.pop().close()
                return

            idx = None
            for i, s in enumerate(self._sinks):
                if s.id == sink_id:
                    idx = i
                    break
            if idx is None:
                raise ValueError(f"Invalid sink id: {sink_id}")
            sink = self._sinks.pop(idx)
            sink.close()

    # --------------------------------------------------------------------- #
    # Logging methods                                                       #
    # --------------------------------------------------------------------- #
    def debug(self, msg, *args, **kwargs):
        self._log("DEBUG", msg, args, kwargs, self._extra)

    def info(self, msg, *args, **kwargs):
        self._log("INFO", msg, args, kwargs, self._extra)

    def warning(self, msg, *args, **kwargs):
        self._log("WARNING", msg, args, kwargs, self._extra)

    def error(self, msg, *args, **kwargs):
        self._log("ERROR", msg, args, kwargs, self._extra)

    def exception(self, msg, *args, **kwargs):
        # Always attach exception info
        self._log("ERROR", msg, args, kwargs, self._extra, opts={"exception": True})

    # --------------------------------------------------------------------- #
    # Context and advanced options                                          #
    # --------------------------------------------------------------------- #
    def bind(self, **kwargs):
        """
        Return a new Logger carrying additional contextual information.
        """
        new_extra = {**self._extra, **kwargs}
        # Share sinks and lock
        return Logger(self._sinks, new_extra, self._lock)

    def opt(self, **opts):
        """
        Return an object that will use given options when logging.
        Supported options: exception (bool)
        """
        return _OptLogger(self, **opts)

    # --------------------------------------------------------------------- #
    # Internal logging implementation                                       #
    # --------------------------------------------------------------------- #
    def _log(self, level_name, message, args, kwargs, extra, opts=None):
        opts = opts or {}
        level_no = _LEVELS[level_name]

        # Format the user message
        if args or kwargs:
            try:
                user_message = message.format(*args, **kwargs)
            except Exception:
                # Fallback similar to Loguru: swallow format errors
                user_message = message
        else:
            user_message = str(message)

        # Exception handling
        if opts.get("exception"):
            exc_text = traceback.format_exc()
            if exc_text.strip() == "NoneType: None":
                # No current exception, ignore
                exc_text = ""
            else:
                user_message = f"{user_message}\n{exc_text.rstrip()}"
        # Build final record for every sink
        record = {
            "time": _now(),
            "level": level_name,
            "message": user_message,
            "extra": _format_extra(extra),
        }

        with self._lock:
            for s in list(self._sinks):
                if level_no < s.level_no:
                    continue
                rendered = s.fmt.format(**record).rstrip()
                s.write(rendered)