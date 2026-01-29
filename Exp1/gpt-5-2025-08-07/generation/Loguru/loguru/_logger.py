import sys
import os
import inspect
import threading
import datetime
import traceback

# Minimal level mapping compatible with common Loguru use
_LEVELS = {
    "TRACE": 5,
    "DEBUG": 10,
    "INFO": 20,
    "SUCCESS": 25,  # Not fully supported, mapped between INFO/WARNING
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
    "EXCEPTION": 40,  # Alias for error with exception
}

_DEFAULT_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}"

def _to_level_no(level):
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        return _LEVELS.get(level.upper(), 0)
    return 0

class _RecordTime:
    """Time formatting compatible with common Loguru-style format specifications.

    Supports tokens: YYYY, MM, DD, HH, mm, ss, SSS
    """
    __slots__ = ("dt",)

    def __init__(self, dt):
        self.dt = dt

    def __str__(self):
        # Default string: ISO-like with millisecond precision
        # Example: 2023-01-01 12:34:56.789
        return self.__format__("YYYY-MM-DD HH:mm:ss.SSS")

    def __format__(self, spec):
        if not spec:
            return str(self)
        # Replace tokens
        dt = self.dt
        # Compute components
        year = f"{dt.year:04d}"
        month = f"{dt.month:02d}"
        day = f"{dt.day:02d}"
        hour = f"{dt.hour:02d}"
        minute = f"{dt.minute:02d}"
        second = f"{dt.second:02d}"
        millisecond = f"{int(dt.microsecond / 1000):03d}"
        result = spec
        # Replace in order to avoid partial token collisions
        result = result.replace("YYYY", year)
        result = result.replace("MM", month)
        result = result.replace("DD", day)
        result = result.replace("HH", hour)
        result = result.replace("mm", minute)
        result = result.replace("ss", second)
        result = result.replace("SSS", millisecond)
        return result

class _Level:
    __slots__ = ("name", "no")

    def __init__(self, name, no):
        self.name = name.upper()
        self.no = int(no)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Level {self.name}:{self.no}>"

class _SinkHandle:
    __slots__ = ("id", "sink", "type", "level", "format", "filter", "owns", "enabled")

    def __init__(self, id_, sink, type_, level, format_, filter_, owns):
        self.id = id_
        self.sink = sink
        self.type = type_  # "function" or "file"
        self.level = level
        self.format = format_ or _DEFAULT_FORMAT
        self.filter = filter_
        self.owns = owns
        self.enabled = True

    def close(self):
        if self.type == "file" and self.owns:
            try:
                self.sink.flush()
            except Exception:
                pass
            try:
                self.sink.close()
            except Exception:
                pass

class Message:
    """Compatibility Message wrapper delivered to sinks if needed.

    In this implementation, callable sinks receive formatted strings.
    This wrapper exists for internal use/extension if desired.

    str(Message) => formatted string
    .record => record dict
    .formatted => pre-formatted string with trailing newline
    """
    __slots__ = ("record", "formatted")

    def __init__(self, record, formatted):
        self.record = record
        self.formatted = formatted

    def __str__(self):
        return self.formatted

class Logger:
    """Minimal Loguru-like logger compatible with core features used in tests."""

    def __init__(self, _handlers=None, _extra=None, _options=None):
        self._handlers = _handlers if _handlers is not None else []
        self._next_id = 1 if not self._handlers else (max(h.id for h in self._handlers) + 1)
        self._lock = threading.RLock()
        self._extra = dict(_extra) if _extra else {}
        # options: depth, exception (False|True|exc|tuple)
        defaults = {"depth": 0, "exception": False}
        if _options:
            defaults.update(_options)
        self._options = defaults

        # If no handlers exist, attach default stderr sink
        if not _handlers:
            # Default sink writes to stderr with default format
            self.add(sys.stderr, level="DEBUG", format=_DEFAULT_FORMAT)

    # Public API

    def add(self, sink, level="DEBUG", format=None, filter=None):
        """Add a sink. Returns a sink id.

        sink can be:
        - a path (str, os.PathLike)
        - a file-like object with write() method
        - a callable accepting a single string argument
        """
        with self._lock:
            lvl = _to_level_no(level)
            owns = False
            sink_type = None
            target = sink

            if isinstance(sink, (str, os.PathLike)):
                # Open the path in append mode, UTF-8
                target = open(sink, "a", encoding="utf-8", buffering=1)
                sink_type = "file"
                owns = True
            elif callable(sink):
                sink_type = "function"
            elif hasattr(sink, "write"):
                sink_type = "file"
            else:
                raise TypeError("Unsupported sink type")

            hid = self._next_id
            self._next_id += 1

            handle = _SinkHandle(hid, target, sink_type, lvl, format, filter, owns)
            self._handlers.append(handle)
            return hid

    def remove(self, handler_id=None):
        """Remove sinks.

        If handler_id is None, remove all sinks and return number removed.
        If handler_id is provided, return True if removed, False if not found.
        """
        with self._lock:
            if handler_id is None:
                count = 0
                while self._handlers:
                    h = self._handlers.pop()
                    h.close()
                    count += 1
                return count
            else:
                for i, h in enumerate(list(self._handlers)):
                    if h.id == handler_id:
                        self._handlers.pop(i)
                        h.close()
                        return True
                return False

    # Binding and options

    def bind(self, **kwargs):
        """Return a child logger with bound context variables."""
        new_extra = dict(self._extra)
        new_extra.update(kwargs)
        return Logger(_handlers=self._handlers, _extra=new_extra, _options=self._options)

    def opt(self, **kwargs):
        """Return a child logger with modified options.

        Supported:
        - depth (int): stack depth added to locate caller
        - exception: True | BaseException | (type, value, tb)
        """
        new_options = dict(self._options)
        new_options.update(kwargs)
        return Logger(_handlers=self._handlers, _extra=self._extra, _options=new_options)

    # Level methods

    def debug(self, message, *args, **kwargs):
        self._log("DEBUG", message, args, kwargs)

    def info(self, message, *args, **kwargs):
        self._log("INFO", message, args, kwargs)

    def warning(self, message, *args, **kwargs):
        self._log("WARNING", message, args, kwargs)

    def error(self, message, *args, **kwargs):
        self._log("ERROR", message, args, kwargs)

    def exception(self, message, *args, **kwargs):
        # Log at ERROR level, capturing current exception
        self.opt(exception=True)._log("ERROR", message, args, kwargs)

    # Internal logging

    def _format_message_with_args(self, message, args, kwargs, extra):
        if not args and not kwargs:
            return str(message)
        # Merge kwargs with bound extras (kwargs take precedence)
        merged = dict(extra)
        merged.update(kwargs)
        try:
            # If positional args are provided, use .format with both
            if args:
                return str(message).format(*args, **merged)
            else:
                # Use format_map with merged to avoid KeyError for missing keys
                class SafeDict(dict):
                    def __missing__(self, k):
                        return "{" + k + "}"
                return str(message).format_map(SafeDict(merged))
        except Exception:
            # Fallback: append arguments representation
            try:
                return f"{message} {args if args else ''} {kwargs if kwargs else ''}".strip()
            except Exception:
                return str(message)

    def _gather_call_site(self, depth):
        # Inspect call stack to get file/function/line
        try:
            frame = inspect.currentframe()
            # Move up: _log -> level method -> user call, plus depth option
            steps = 3 + int(depth)
            for _ in range(steps):
                if frame is not None:
                    frame = frame.f_back
            if frame is None:
                raise RuntimeError
            code = frame.f_code
            filename = code.co_filename
            function = code.co_name
            line = frame.f_lineno
            module = frame.f_globals.get("__name__", "")
            return filename, function, line, module
        except Exception:
            return "<unknown>", "<unknown>", 0, "<unknown>"

    def _build_record(self, level_name, raw_message, args, kwargs):
        # Time
        now = datetime.datetime.now()
        rtime = _RecordTime(now)
        level_no = _to_level_no(level_name)
        level = _Level(level_name, level_no)

        # Exception handling option
        exc_opt = self._options.get("exception", False)
        exception_text = self._compute_exception_text(exc_opt)

        # Message formatting including bound context
        message = self._format_message_with_args(raw_message, args, kwargs, self._extra)

        filename, function, line, module = self._gather_call_site(self._options.get("depth", 0))

        record = {
            "time": rtime,
            "level": level,
            "message": message,
            "exception": exception_text or "",
            "file": filename,
            "name": module,
            "function": function,
            "line": line,
            "extra": dict(self._extra),
            "thread": threading.current_thread().name,
            "process": os.getpid(),
        }
        return record

    def _compute_exception_text(self, exc_opt):
        if not exc_opt:
            return None
        # exc_opt True -> capture current exception if present
        if exc_opt is True:
            etype, evalue, tb = sys.exc_info()
            if etype is None:
                return None
            return "".join(traceback.format_exception(etype, evalue, tb)).rstrip()
        # exc_opt can be BaseException
        if isinstance(exc_opt, BaseException):
            return "".join(traceback.format_exception(type(exc_opt), exc_opt, exc_opt.__traceback__)).rstrip()
        # exc_opt can be (etype, value, tb)
        if isinstance(exc_opt, tuple) and len(exc_opt) == 3:
            etype, evalue, tb = exc_opt
            return "".join(traceback.format_exception(etype, evalue, tb)).rstrip()
        # Unknown type
        return None

    def _format_record(self, record, fmt):
        # Provide a formatting mapping accessible via {key} in fmt
        # Level: ensure it's formatted as its name (string)
        level_str = str(record["level"])
        mapping = {
            "time": record["time"],
            "level": level_str,
            "message": record["message"],
            "exception": record.get("exception", ""),
            "file": record.get("file", ""),
            "name": record.get("name", ""),
            "function": record.get("function", ""),
            "line": record.get("line", 0),
            "extra": record.get("extra", {}),
            "thread": record.get("thread", ""),
            "process": record.get("process", 0),
        }
        try:
            formatted = fmt.format(**mapping)
        except Exception:
            # Fallback to default format if the provided format fails
            formatted = _DEFAULT_FORMAT.format(**mapping)
        # Append exception if not included in format and exists
        if record.get("exception"):
            # If format string did not include {exception}, append it on a new line
            if "{exception" not in fmt:
                formatted = f"{formatted}\n{record['exception']}"
        # Ensure trailing newline
        if not formatted.endswith("\n"):
            formatted += "\n"
        return formatted

    def _log(self, level_name, message, args, kwargs):
        record = self._build_record(level_name, message, args, kwargs)

        with self._lock:
            for handle in list(self._handlers):
                if not handle.enabled:
                    continue
                if record["level"].no < handle.level:
                    continue
                # Apply filter if present; filter receives the record dict
                if handle.filter:
                    try:
                        if not handle.filter(record):
                            continue
                    except Exception:
                        # If filter fails, skip logging to this sink
                        continue
                formatted = self._format_record(record, handle.format)
                # Deliver to sink
                try:
                    if handle.type == "function":
                        # Callable sinks receive the formatted string
                        handle.sink(formatted)
                    elif handle.type == "file":
                        handle.sink.write(formatted)
                        try:
                            handle.sink.flush()
                        except Exception:
                            pass
                    else:
                        # Unknown type, ignore
                        pass
                except Exception:
                    # Silently ignore sink errors to remain robust
                    pass

    # Representations
    def __repr__(self):
        return f"<Logger handlers={len(self._handlers)} extra={self._extra} options={self._options}>"