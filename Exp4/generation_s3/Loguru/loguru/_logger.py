from __future__ import annotations

import datetime as _dt
import inspect as _inspect
import os as _os
import sys as _sys
import threading as _threading
import traceback as _traceback
from dataclasses import dataclass as _dataclass
from types import SimpleNamespace as _SimpleNamespace
from typing import Any, Callable, Dict, Optional, Tuple, Union


def _format_time(dt: _dt.datetime) -> str:
    # Deterministic local time formatting with milliseconds: "YYYY-MM-DD HH:MM:SS.mmm"
    # Use dt.strftime for fixed width and ensure milliseconds are zero padded.
    return dt.strftime("%Y-%m-%d %H:%M:%S.") + f"{int(dt.microsecond / 1000):03d}"


class _ExtraDict(dict):
    """Dict that supports format-style indexing in {extra[key]}."""

    def __missing__(self, key):
        raise KeyError(key)


class _FormatMap(dict):
    """Mapping that allows {key} and {key[sub]} access during str.format_map()."""

    def __missing__(self, key):
        return "{" + str(key) + "}"


def _coerce_level(level: Union[str, int]) -> Tuple[str, int]:
    if isinstance(level, int):
        return (str(level), int(level))
    if not isinstance(level, str):
        raise ValueError(f"Invalid level: {level!r}")
    name = level.upper()
    if name not in Logger._LEVELS:
        raise ValueError(f"Invalid level name: {level!r}")
    return (name, Logger._LEVELS[name]["no"])


def _stringify_message(message: Any, args: Tuple[Any, ...], kwargs: Dict[str, Any], lazy: bool) -> str:
    try:
        if lazy and callable(message):
            message = message()
        # Common Loguru usage: "Hello {}", name
        if isinstance(message, str):
            if "{}" in message or "{" in message:
                # Try format with args/kwargs.
                try:
                    return message.format(*args, **kwargs)
                except Exception:
                    # Fallback: try to stringify without raising.
                    return str(message) + ("" if not args and not kwargs else " " + repr(args if args else kwargs))
            if args or kwargs:
                # Still try .format for patterns without braces in tests.
                try:
                    return message.format(*args, **kwargs)
                except Exception:
                    return str(message) + " " + repr(args if args else kwargs)
            return message
        # Non-string message
        if args or kwargs:
            # Best effort: if message is format-capable, try.
            try:
                return str(message).format(*args, **kwargs)
            except Exception:
                return str(message) + " " + repr(args if args else kwargs)
        return str(message)
    except Exception:
        # Last-resort: never crash logging.
        try:
            return repr(message)
        except Exception:
            return "<unprintable message>"


def _render_exception(exc_info: Optional[Tuple[type, BaseException, Any]]) -> str:
    if not exc_info or exc_info == (None, None, None):
        return ""
    try:
        return "".join(_traceback.format_exception(*exc_info)).rstrip("\n")
    except Exception:
        return "Exception (unable to format traceback)"


def _caller_info(depth: int) -> Dict[str, Any]:
    # Determine the caller module/function/line. Depth is relative to the logging call.
    # We add a constant offset to skip internal frames.
    # This doesn't need to be perfect; it must be stable enough for prefix activation tests.
    frame = None
    try:
        # 0: _caller_info
        # 1: _log
        # 2: public method (info/debug/...)
        # 3+: user code (plus opt(depth))
        stack = _inspect.stack()
        idx = 3 + max(0, int(depth))
        if idx >= len(stack):
            idx = len(stack) - 1
        frameinfo = stack[idx]
        frame = frameinfo.frame
        module = _inspect.getmodule(frame)
        name = module.__name__ if module and hasattr(module, "__name__") else "__main__"
        return {
            "name": name,
            "function": frameinfo.function,
            "line": frameinfo.lineno,
            "file": frameinfo.filename,
        }
    except Exception:
        return {"name": "__main__", "function": "<unknown>", "line": 0, "file": ""}
    finally:
        # Avoid reference cycles from frames.
        try:
            del frame
        except Exception:
            pass


@_dataclass
class _Handler:
    id: int
    sink: Any
    levelno: int
    format: Union[str, Callable[[Dict[str, Any]], str]]
    filter: Any
    colorize: bool
    serialize: bool
    backtrace: bool
    diagnose: bool
    enqueue: bool
    catch: bool
    _file: Any = None  # opened file handle for path sinks

    def close(self) -> None:
        if self._file is not None:
            try:
                self._file.close()
            except Exception:
                pass
            self._file = None


class Logger:
    _LEVELS = {
        "TRACE": {"name": "TRACE", "no": 5},
        "DEBUG": {"name": "DEBUG", "no": 10},
        "INFO": {"name": "INFO", "no": 20},
        "SUCCESS": {"name": "SUCCESS", "no": 25},
        "WARNING": {"name": "WARNING", "no": 30},
        "ERROR": {"name": "ERROR", "no": 40},
        "CRITICAL": {"name": "CRITICAL", "no": 50},
    }

    def __init__(
        self,
        *,
        _core: "Logger._Core",
        _extra: Optional[Dict[str, Any]] = None,
        _options: Optional[Dict[str, Any]] = None,
    ):
        self._core = _core
        self._extra = dict(_extra or {})
        self._options = dict(_options or {})

    class _Core:
        def __init__(self):
            self.handlers: Dict[int, _Handler] = {}
            self.handlers_order: list[int] = []
            self.next_id: int = 1
            self.lock = _threading.RLock()
            self.extra: Dict[str, Any] = {}
            # Activation rules: prefix -> enabled(bool). Default is enabled.
            self.activation: Dict[str, bool] = {}

    # --- Public API ---

    def add(
        self,
        sink,
        *,
        level: Union[str, int] = "DEBUG",
        format: Union[str, Callable[[Dict[str, Any]], str]] = "{time} | {level} | {message}",
        filter=None,
        colorize: bool = False,
        serialize: bool = False,
        backtrace: bool = False,
        diagnose: bool = False,
        enqueue: bool = False,
        catch: bool = True,
        **kwargs,
    ) -> int:
        # kwargs accepted for compatibility; ignored.
        _, levelno = _coerce_level(level)

        with self._core.lock:
            hid = self._core.next_id
            self._core.next_id += 1

            h = _Handler(
                id=hid,
                sink=sink,
                levelno=levelno,
                format=format,
                filter=filter,
                colorize=colorize,
                serialize=serialize,
                backtrace=backtrace,
                diagnose=diagnose,
                enqueue=enqueue,
                catch=catch,
            )

            # Prepare sink
            if isinstance(sink, (str, bytes, _os.PathLike)):
                path = _os.fspath(sink)
                # newline="" prevents newline translation; encoding fixed for determinism.
                h._file = open(path, "a", encoding="utf-8", newline="")
            else:
                h._file = None

            self._core.handlers[hid] = h
            self._core.handlers_order.append(hid)
            return hid

    def remove(self, handler_id: Optional[int] = None) -> None:
        with self._core.lock:
            if handler_id is None:
                # Close all and clear
                for hid in list(self._core.handlers_order):
                    h = self._core.handlers.get(hid)
                    if h:
                        h.close()
                self._core.handlers.clear()
                self._core.handlers_order.clear()
                return

            h = self._core.handlers.pop(handler_id, None)
            if h is None:
                return
            h.close()
            try:
                self._core.handlers_order.remove(handler_id)
            except ValueError:
                pass

    def bind(self, **kwargs) -> "Logger":
        extra = dict(self._extra)
        extra.update(kwargs)
        return Logger(_core=self._core, _extra=extra, _options=self._options)

    def opt(
        self,
        *,
        depth: int = 0,
        exception=None,
        record: bool = False,
        lazy: bool = False,
        colors: bool = False,
        raw: bool = False,
        capture: bool = True,
        ansi: bool = False,
    ) -> "Logger":
        # Only subset used; keep all flags for API compatibility.
        options = dict(self._options)
        options.update(
            {
                "depth": depth,
                "exception": exception,
                "record": record,
                "lazy": lazy,
                "colors": colors,
                "raw": raw,
                "capture": capture,
                "ansi": ansi,
            }
        )
        return Logger(_core=self._core, _extra=self._extra, _options=options)

    def log(self, level: Union[str, int], message: Any, *args, **kwargs) -> None:
        name, no = _coerce_level(level)
        self._log(name, no, message, args, kwargs)

    def debug(self, message: Any, *args, **kwargs) -> None:
        self._log("DEBUG", self._LEVELS["DEBUG"]["no"], message, args, kwargs)

    def info(self, message: Any, *args, **kwargs) -> None:
        self._log("INFO", self._LEVELS["INFO"]["no"], message, args, kwargs)

    def warning(self, message: Any, *args, **kwargs) -> None:
        self._log("WARNING", self._LEVELS["WARNING"]["no"], message, args, kwargs)

    def error(self, message: Any, *args, **kwargs) -> None:
        self._log("ERROR", self._LEVELS["ERROR"]["no"], message, args, kwargs)

    def exception(self, message: Any, *args, **kwargs) -> None:
        # Capture current exception
        self.opt(exception=True)._log("ERROR", self._LEVELS["ERROR"]["no"], message, args, kwargs)

    def enable(self, name: str) -> None:
        with self._core.lock:
            self._core.activation[str(name)] = True

    def disable(self, name: str) -> None:
        with self._core.lock:
            self._core.activation[str(name)] = False

    def level(self, name: str, no=None, color=None, icon=None):
        # Minimal: return dict-like level info; allow retrieval only.
        uname = str(name).upper()
        if uname not in self._LEVELS:
            if no is None:
                raise ValueError(f"Level does not exist: {name!r}")
            # allow defining new levels minimally
            self._LEVELS[uname] = {"name": uname, "no": int(no)}
        return dict(self._LEVELS[uname])

    def configure(self, *, handlers=None, levels=None, extra=None, patcher=None, activation=None) -> None:
        # Minimal compatibility:
        # - handlers: list of dicts for add()
        # - extra: default extra dict
        # - activation: list/tuple of (prefix, enabled) or dict mapping
        if levels:
            # Support dict/list defining levels minimally.
            try:
                if isinstance(levels, dict):
                    for lname, ldef in levels.items():
                        if isinstance(ldef, dict):
                            self.level(lname, no=ldef.get("no"))
                        else:
                            self.level(lname, no=ldef)
                else:
                    for ldef in levels:
                        if isinstance(ldef, dict):
                            self.level(ldef.get("name"), no=ldef.get("no"))
            except Exception:
                pass

        if extra is not None:
            with self._core.lock:
                self._core.extra = dict(extra)

        if activation is not None:
            with self._core.lock:
                if isinstance(activation, dict):
                    self._core.activation.update({str(k): bool(v) for k, v in activation.items()})
                else:
                    # expected iterable of (prefix, enabled)
                    for item in activation:
                        try:
                            prefix, enabled = item
                            self._core.activation[str(prefix)] = bool(enabled)
                        except Exception:
                            continue

        if handlers is not None:
            # Replace all handlers
            self.remove()
            for h in handlers:
                if isinstance(h, dict):
                    sink = h.get("sink")
                    if sink is None and "path" in h:
                        sink = h["path"]
                    if sink is None:
                        continue
                    params = dict(h)
                    params.pop("sink", None)
                    params.pop("path", None)
                    self.add(sink, **params)

        # patcher ignored in this subset

    # --- Internals ---

    def _is_enabled_for(self, record_name: str) -> bool:
        # Prefix-based activation rules. Default is enabled.
        # Most specific (longest) matching prefix wins.
        with self._core.lock:
            best_len = -1
            best_val = True
            for prefix, enabled in self._core.activation.items():
                if record_name == prefix or record_name.startswith(prefix + ".") or record_name.startswith(prefix):
                    # Accept both exact and prefix matching.
                    if len(prefix) > best_len:
                        best_len = len(prefix)
                        best_val = enabled
            return best_val

    def _filter_allows(self, flt, record: Dict[str, Any]) -> bool:
        if flt is None:
            return True
        try:
            if callable(flt):
                return bool(flt(record))
            if isinstance(flt, str):
                return str(record.get("name", "")).startswith(flt)
            if isinstance(flt, dict):
                # Mapping of prefix -> enabled
                name = str(record.get("name", ""))
                best_len = -1
                best_val = True
                for prefix, enabled in flt.items():
                    prefix = str(prefix)
                    if name == prefix or name.startswith(prefix + ".") or name.startswith(prefix):
                        if len(prefix) > best_len:
                            best_len = len(prefix)
                            best_val = bool(enabled)
                return best_val
        except Exception:
            return True
        return True

    def _log(self, level_name: str, level_no: int, message: Any, args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> None:
        options = self._options
        depth = int(options.get("depth", 0) or 0)
        lazy = bool(options.get("lazy", False))
        raw = bool(options.get("raw", False))

        caller = _caller_info(depth)
        record_name = caller.get("name", "__main__")
        if not self._is_enabled_for(record_name):
            return

        # Determine exception
        exc_info = None
        exc_opt = options.get("exception", None)
        if exc_opt is True:
            exc_info = _sys.exc_info()
            if exc_info == (None, None, None):
                exc_info = None
        elif isinstance(exc_opt, BaseException):
            exc_info = (type(exc_opt), exc_opt, exc_opt.__traceback__)
        elif isinstance(exc_opt, tuple) and len(exc_opt) == 3:
            exc_info = exc_opt
        elif exc_opt:
            # any truthy other: try to capture current
            exc_info = _sys.exc_info()
            if exc_info == (None, None, None):
                exc_info = None

        dt = _dt.datetime.now()
        text = _stringify_message(message, args, kwargs, lazy=lazy)

        extra = _ExtraDict()
        # Merge core extra, bound extra. Bound extra should override core.
        with self._core.lock:
            extra.update(self._core.extra)
        extra.update(self._extra)

        record: Dict[str, Any] = {
            "time": dt,
            "level": {"name": level_name, "no": level_no},
            "message": text,
            "extra": extra,
            "exception": exc_info,
            "name": record_name,
            "function": caller.get("function"),
            "line": caller.get("line"),
            "file": caller.get("file"),
        }

        # Render exception text once per record for consistency
        exc_text = _render_exception(exc_info)

        # Emit to handlers in add order
        with self._core.lock:
            handler_ids = list(self._core.handlers_order)
            handlers = [self._core.handlers.get(hid) for hid in handler_ids]

        for h in handlers:
            if h is None:
                continue
            if level_no < h.levelno:
                continue
            if not self._filter_allows(h.filter, record):
                continue

            try:
                if raw:
                    out = text
                    # In Loguru, raw means no automatic newline. Keep exact as message.
                else:
                    out = self._format_record(h.format, record, exc_text)
                    if not out.endswith("\n"):
                        out += "\n"
                self._write_to_sink(h, out)
            except Exception:
                if h.catch:
                    continue
                raise

    def _format_record(self, fmt: Union[str, Callable[[Dict[str, Any]], str]], record: Dict[str, Any], exc_text: str) -> str:
        if callable(fmt):
            # Callable formatter returns final string.
            try:
                return str(fmt(record))
            except Exception:
                # fallback to minimal
                return f"{_format_time(record['time'])} | {record['level']['name']} | {record['message']}"

        # String formatter with placeholders
        time_str = _format_time(record["time"])
        level_str = record["level"]["name"]
        msg_str = record["message"]

        mapping = _FormatMap()
        mapping.update(
            {
                "time": time_str,
                "level": level_str,
                "message": msg_str,
                "extra": record.get("extra", {}),
                "exception": exc_text,
                "name": record.get("name", ""),
                "function": record.get("function", ""),
                "line": record.get("line", 0),
                "file": record.get("file", ""),
                "record": record,  # sometimes useful in tests/format strings
            }
        )

        try:
            out = str(fmt).format_map(mapping)
        except Exception:
            # Basic fallback, still include exception if any.
            out = f"{time_str} | {level_str} | {msg_str}"
            if exc_text:
                out += "\n" + exc_text

        # If exception exists and placeholder not used, append it.
        if exc_text and "{exception" not in str(fmt) and "{exception}" not in str(fmt):
            # Append on a new line
            if out and not out.endswith("\n"):
                out += "\n"
            out += exc_text
        return out

    def _write_to_sink(self, h: _Handler, out: str) -> None:
        sink = h.sink
        if h._file is not None:
            h._file.write(out)
            try:
                h._file.flush()
            except Exception:
                pass
            return

        # file-like object
        if hasattr(sink, "write") and callable(getattr(sink, "write")):
            sink.write(out)
            if hasattr(sink, "flush") and callable(getattr(sink, "flush")):
                try:
                    sink.flush()
                except Exception:
                    pass
            return

        # callable sink
        if callable(sink):
            sink(out)
            return

        # Unknown sink type: ignore (Loguru would raise at add time, but keep robust)
        return


# Singleton instance
logger = Logger(_core=Logger._Core())