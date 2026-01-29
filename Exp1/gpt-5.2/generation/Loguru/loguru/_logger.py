from __future__ import annotations

import datetime as _dt
import inspect as _inspect
import io as _io
import os as _os
import sys as _sys
import threading as _threading
import traceback as _traceback
from dataclasses import dataclass as _dataclass
from typing import Any, Callable, Dict, Optional, Tuple, Union


# ---- Levels ----

_LEVELS: Dict[str, Tuple[int, str]] = {
    "TRACE": (5, "TRACE"),
    "DEBUG": (10, "DEBUG"),
    "INFO": (20, "INFO"),
    "SUCCESS": (25, "SUCCESS"),
    "WARNING": (30, "WARNING"),
    "ERROR": (40, "ERROR"),
    "CRITICAL": (50, "CRITICAL"),
}

_NAME_FROM_NO = {no: name for name, (no, _) in _LEVELS.items()}


def _level_to_no(level: Union[str, int]) -> int:
    if isinstance(level, int):
        return level
    u = str(level).upper()
    if u in _LEVELS:
        return _LEVELS[u][0]
    # Best effort: parse ints in string
    try:
        return int(level)
    except Exception:
        return 0


def _level_name(level: Union[str, int]) -> str:
    if isinstance(level, str):
        u = level.upper()
        if u in _LEVELS:
            return _LEVELS[u][1]
        return level
    # int
    return _NAME_FROM_NO.get(level, str(level))


# ---- Record / formatting helpers ----

def _now() -> _dt.datetime:
    # Local time with timezone if available; keep deterministic-ish representation
    return _dt.datetime.now().astimezone()


def _format_time(dt: _dt.datetime, fmt: Optional[str] = None) -> str:
    if fmt is None:
        # Close to Loguru default prefix time formatting.
        # Example: 2020-01-01 12:00:00.123
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return dt.strftime(fmt)


def _safe_format_message(message: str, args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
    if args or kwargs:
        try:
            # Loguru uses "{}" formatting by default (str.format)
            return message.format(*args, **kwargs)
        except Exception:
            # Fallback: mimic logging module behavior
            try:
                return message % args
            except Exception:
                return message
    return message


def _stringify_extra(extra: Dict[str, Any]) -> str:
    if not extra:
        return "{}"
    # Match Loguru-ish representation: dict with repr values
    # Keep order deterministic: insertion order in Python 3.7+
    items = ", ".join(f"{k}={v!r}" for k, v in extra.items())
    return "{" + items + "}"


def _exception_text(exc_info) -> str:
    if not exc_info:
        return ""
    etype, evalue, tb = exc_info
    lines = _traceback.format_exception(etype, evalue, tb)
    return "".join(lines).rstrip("\n")


def _default_format(record: Dict[str, Any]) -> str:
    # A simplified default resembling loguru default:
    # "{time} | {level} | {message}"
    # Append extras if any, then exception if any (on new line).
    t = record["time"]
    level = record["level"]["name"]
    msg = record["message"]
    extra = record.get("extra") or {}
    exc = record.get("exception")
    out = f"{_format_time(t)} | {level:<8} | {msg}"
    if extra:
        out += f" | extra={_stringify_extra(extra)}"
    if exc:
        out += "\n" + exc
    return out + "\n"


def _apply_format(fmt: Union[str, Callable[[Dict[str, Any]], str]], record: Dict[str, Any]) -> str:
    if callable(fmt):
        try:
            res = fmt(record)
            if not res.endswith("\n"):
                res += "\n"
            return res
        except Exception:
            # If formatter fails, fallback to default format
            return _default_format(record)

    # String format: support common Loguru fields.
    # Provide keys: time, level, message, extra, exception, name, function, line, file, module, thread, process
    mapping = {
        "time": record["time"],
        "message": record["message"],
        "level": record["level"],
        "extra": record.get("extra") or {},
        "exception": record.get("exception") or "",
        "name": record.get("name") or "",
        "function": record.get("function") or "",
        "line": record.get("line") or 0,
        "file": record.get("file") or {"name": "", "path": ""},
        "module": record.get("module") or "",
        "thread": record.get("thread") or {"id": 0, "name": ""},
        "process": record.get("process") or {"id": 0, "name": ""},
    }

    class _LevelProxy:
        def __init__(self, d):  # d: {"name":, "no":}
            self.name = d.get("name")
            self.no = d.get("no")

        def __str__(self):
            return str(self.name)

    class _FileProxy:
        def __init__(self, d):
            self.name = d.get("name", "")
            self.path = d.get("path", "")

        def __str__(self):
            return self.name

    class _TimeProxy:
        def __init__(self, dt):
            self._dt = dt

        def __str__(self):
            return _format_time(self._dt)

        def __format__(self, spec):
            # Allow "{time:%Y-%m-%d}" formatting
            if spec:
                return _format_time(self._dt, spec)
            return _format_time(self._dt)

    class _ThreadProxy:
        def __init__(self, d):
            self.id = d.get("id", 0)
            self.name = d.get("name", "")

        def __str__(self):
            return str(self.name or self.id)

    class _ProcessProxy(_ThreadProxy):
        pass

    proxy = dict(mapping)
    proxy["level"] = _LevelProxy(mapping["level"])
    proxy["file"] = _FileProxy(mapping["file"])
    proxy["time"] = _TimeProxy(mapping["time"])
    proxy["thread"] = _ThreadProxy(mapping["thread"])
    proxy["process"] = _ProcessProxy(mapping["process"])

    # Also allow direct {extra[key]} in format string by exposing extra dict itself.
    try:
        res = fmt.format_map(_SafeDict(proxy))
    except KeyError:
        # Missing fields: best effort default
        res = _default_format(record).rstrip("\n")
    except Exception:
        res = _default_format(record).rstrip("\n")

    if not res.endswith("\n"):
        res += "\n"
    return res


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


# ---- Sink handling ----

@_dataclass
class _Sink:
    id: int
    target: Any  # callable or file-like
    format: Union[str, Callable[[Dict[str, Any]], str]]
    level_no: int
    enabled: bool = True
    enqueue: bool = False  # ignored
    catch: bool = True
    colorize: bool = False  # ignored
    backtrace: bool = False  # ignored
    diagnose: bool = False  # ignored
    _owns_stream: bool = False

    def write(self, text: str):
        if not self.enabled:
            return
        # callable sink receives message string (like Loguru) OR record? Commonly string.
        if callable(self.target) and not hasattr(self.target, "write"):
            self.target(text)
        else:
            self.target.write(text)
            if hasattr(self.target, "flush"):
                self.target.flush()

    def close(self):
        if self._owns_stream and hasattr(self.target, "close"):
            try:
                self.target.close()
            except Exception:
                pass


# ---- Logger implementation ----

class Logger:
    def __init__(self, *, _extra: Optional[Dict[str, Any]] = None, _options: Optional[Dict[str, Any]] = None):
        self._lock = _threading.RLock()
        self._sinks: Dict[int, _Sink] = {}
        self._next_id = 1
        self._extra = dict(_extra or {})
        self._options = dict(_options or {})
        # Basic enable/disable per logger instance
        self._enabled = True

    # --- configuration ---

    def add(
        self,
        sink: Union[str, _io.TextIOBase, Callable[[str], Any]],
        *,
        level: Union[str, int] = "DEBUG",
        format: Union[str, Callable[[Dict[str, Any]], str]] = "{time} | {level} | {message}",
        filter: Any = None,  # ignored
        colorize: bool = False,
        serialize: bool = False,  # ignored
        backtrace: bool = False,
        diagnose: bool = False,
        enqueue: bool = False,
        catch: bool = True,
        encoding: str = "utf-8",
        **kwargs,
    ) -> int:
        level_no = _level_to_no(level)
        target = sink
        owns = False
        if isinstance(sink, (str, _os.PathLike)):
            path = _os.fspath(sink)
            # Ensure directory exists if needed
            parent = _os.path.dirname(path)
            if parent:
                try:
                    _os.makedirs(parent, exist_ok=True)
                except Exception:
                    pass
            target = open(path, "a", encoding=encoding, newline="")  # newline preserved
            owns = True

        with self._lock:
            sid = self._next_id
            self._next_id += 1
            self._sinks[sid] = _Sink(
                id=sid,
                target=target,
                format=format,
                level_no=level_no,
                enabled=True,
                enqueue=enqueue,
                catch=catch,
                colorize=colorize,
                backtrace=backtrace,
                diagnose=diagnose,
                _owns_stream=owns,
            )
            return sid

    def remove(self, handler_id: Optional[int] = None) -> None:
        with self._lock:
            if handler_id is None:
                ids = list(self._sinks.keys())
            else:
                ids = [handler_id] if handler_id in self._sinks else []
            for sid in ids:
                s = self._sinks.pop(sid, None)
                if s:
                    s.close()

    # --- context / options ---

    def bind(self, **kwargs) -> "Logger":
        extra = dict(self._extra)
        extra.update(kwargs)
        return Logger(_extra=extra, _options=self._options)

    def opt(
        self,
        *,
        exception: Union[bool, BaseException, Tuple[Any, Any, Any]] = False,
        depth: int = 0,
        ansi: bool = False,  # ignored
        lazy: bool = False,  # ignored
        record: bool = False,  # ignored
        capture: bool = True,  # ignored
        colors: bool = False,  # ignored
        raw: bool = False,
    ) -> "Logger":
        options = dict(self._options)
        options.update(
            {
                "exception": exception,
                "depth": depth,
                "raw": raw,
            }
        )
        return Logger(_extra=self._extra, _options=options)

    def enable(self, name: Optional[str] = None) -> None:
        # minimal compat: enable this logger (ignore name)
        self._enabled = True

    def disable(self, name: Optional[str] = None) -> None:
        self._enabled = False

    # --- logging ---

    def log(self, level: Union[str, int], message: str, *args, **kwargs) -> None:
        if not self._enabled:
            return

        level_no = _level_to_no(level)
        level_name = _level_name(level)

        # Determine exception info from .opt(exception=...)
        exc_text = ""
        exc_info = None
        opt_exc = self._options.get("exception", False)
        if opt_exc:
            if opt_exc is True:
                exc_info = _sys.exc_info()
            elif isinstance(opt_exc, BaseException):
                exc_info = (type(opt_exc), opt_exc, opt_exc.__traceback__)
            elif isinstance(opt_exc, tuple) and len(opt_exc) == 3:
                exc_info = opt_exc
            else:
                exc_info = _sys.exc_info()
        if exc_info and exc_info[0] is not None:
            exc_text = _exception_text(exc_info)

        # Compute caller info (depth + internal frames)
        depth = int(self._options.get("depth", 0) or 0)
        frame = _inspect.currentframe()
        # Walk: current -> log -> level method -> user ; plus optional depth
        # We attempt to skip internal frames belonging to this module.
        try:
            f = frame
            # skip current frame and internal frames
            steps = 0
            while f and steps < 50:
                code = f.f_code
                mod = f.f_globals.get("__name__", "")
                if mod != __name__:
                    break
                f = f.f_back
                steps += 1
            # apply extra depth
            for _ in range(depth):
                if f and f.f_back:
                    f = f.f_back
            if not f:
                f = frame
            info = _inspect.getframeinfo(f)
            file_path = info.filename
            file_name = _os.path.basename(file_path)
            function = info.function
            line = info.lineno
            module = _os.path.splitext(file_name)[0]
            name = f.f_globals.get("__name__", "")
        except Exception:
            file_path = ""
            file_name = ""
            function = ""
            line = 0
            module = ""
            name = ""
        finally:
            try:
                del frame
            except Exception:
                pass

        msg = _safe_format_message(message, args, kwargs)
        raw = bool(self._options.get("raw", False))
        t = _now()
        thread = _threading.current_thread()
        process_id = _os.getpid()
        record = {
            "time": t,
            "message": msg,
            "level": {"name": level_name, "no": level_no},
            "extra": dict(self._extra),
            "exception": exc_text if exc_text else None,
            "file": {"name": file_name, "path": file_path},
            "function": function,
            "line": line,
            "module": module,
            "name": name,
            "thread": {"id": thread.ident or 0, "name": thread.name},
            "process": {"id": process_id, "name": ""},
        }

        with self._lock:
            sinks = list(self._sinks.values())

        for sink in sinks:
            if not sink.enabled:
                continue
            if level_no < sink.level_no:
                continue
            try:
                if raw:
                    text = msg
                    if not text.endswith("\n"):
                        text += "\n"
                else:
                    text = _apply_format(sink.format, record)
                sink.write(text)
            except Exception:
                if sink.catch:
                    # swallow like loguru's catch=True
                    continue
                raise

    # convenience methods
    def debug(self, message: str, *args, **kwargs) -> None:
        self.log("DEBUG", message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        self.log("INFO", message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        self.log("WARNING", message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        self.log("ERROR", message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> None:
        # Like Loguru: logs with ERROR and exception from current context
        self.opt(exception=True, depth=1).log("ERROR", message, *args, **kwargs)


# singleton logger
logger = Logger()