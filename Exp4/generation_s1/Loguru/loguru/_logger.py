import datetime as _datetime
import os as _os
import sys as _sys
import threading as _threading
import traceback as _traceback
from dataclasses import dataclass as _dataclass
from types import SimpleNamespace as _SimpleNamespace


def _level_from_name(name: str) -> int:
    name = str(name).upper()
    if name not in _LEVELS_BY_NAME:
        raise ValueError(f"Unknown level: {name!r}")
    return _LEVELS_BY_NAME[name].no


@_dataclass(frozen=True)
class Level:
    name: str
    no: int
    icon: str = ""


_LEVELS = [
    Level("TRACE", 5),
    Level("DEBUG", 10),
    Level("INFO", 20),
    Level("SUCCESS", 25),
    Level("WARNING", 30),
    Level("ERROR", 40),
    Level("CRITICAL", 50),
]
_LEVELS_BY_NAME = {lvl.name: lvl for lvl in _LEVELS}
_LEVELS_BY_NO = {lvl.no: lvl for lvl in _LEVELS}


def _resolve_level(level):
    if isinstance(level, int):
        no = level
        if no in _LEVELS_BY_NO:
            return _LEVELS_BY_NO[no]
        return Level(str(level), no)
    if isinstance(level, Level):
        return level
    if isinstance(level, str):
        return _LEVELS_BY_NAME[str(level).upper()]
    raise TypeError(f"Invalid level type: {type(level)!r}")


class Message:
    def __init__(self, text: str, record: dict):
        self._text = text
        self.record = record

    def __str__(self):
        return self._text

    def __repr__(self):
        return self._text


class _FormatProxy:
    """
    Helper to allow attribute access and nested dict access in str.format().
    """

    __slots__ = ("_obj",)

    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, item):
        obj = self._obj
        if isinstance(obj, dict):
            if item in obj:
                return _wrap(obj[item])
            raise AttributeError(item)
        try:
            return _wrap(getattr(obj, item))
        except AttributeError:
            raise

    def __getitem__(self, item):
        obj = self._obj
        if isinstance(obj, dict):
            return _wrap(obj[item])
        return _wrap(obj[item])

    def __str__(self):
        return str(self._obj)

    def __format__(self, spec):
        return format(self._obj, spec)


def _wrap(v):
    if isinstance(v, (dict, _SimpleNamespace, Level)):
        return _FormatProxy(v)
    return v


def _format_time(dt: _datetime.datetime, spec: str | None):
    if not spec:
        return dt.isoformat(sep=" ", timespec="milliseconds")
    s = spec
    ms = f"{int(dt.microsecond / 1000):03d}"
    s = s.replace("SSS", ms)
    s = s.replace("YYYY", f"{dt.year:04d}")
    s = s.replace("MM", f"{dt.month:02d}")
    s = s.replace("DD", f"{dt.day:02d}")
    s = s.replace("HH", f"{dt.hour:02d}")
    s = s.replace("mm", f"{dt.minute:02d}")
    s = s.replace("ss", f"{dt.second:02d}")
    return s


class _TimeWrapper:
    __slots__ = ("_dt",)

    def __init__(self, dt: _datetime.datetime):
        self._dt = dt

    def __format__(self, spec: str):
        return _format_time(self._dt, spec)

    def __str__(self):
        return _format_time(self._dt, None)


DEFAULT_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}\n"


class _FileSink:
    def __init__(self, path: str, encoding: str = "utf-8"):
        self._path = path
        self._encoding = encoding
        self._fh = open(path, "a", encoding=encoding, newline="")

    def write(self, s: str):
        self._fh.write(s)
        self._fh.flush()

    def close(self):
        try:
            self._fh.close()
        except Exception:
            pass


@_dataclass
class _Handler:
    id: int
    sink: object
    levelno: int
    fmt: str
    flt: object = None
    enabled: bool = True
    is_path: bool = False

    def close(self):
        if self.is_path and hasattr(self.sink, "close"):
            self.sink.close()


class Logger:
    def __init__(self, *, _extra=None, _options=None, _core=None):
        if _core is None:
            _core = {
                "handlers": [],
                "handler_id": 0,
                "disabled_prefixes": set(),
                "extra": {},
            }
        self._core = _core
        self._extra = dict(_extra or {})
        self._options = dict(_options or {})

    # --- public api ---

    def add(
        self,
        sink,
        *,
        level="DEBUG",
        format=DEFAULT_FORMAT,
        filter=None,
        colorize=False,
        enqueue=False,
        backtrace=False,
        diagnose=False,
        catch=True,
        serialize=False,
        **kwargs,
    ):
        level_obj = _resolve_level(level)
        self._core["handler_id"] += 1
        hid = self._core["handler_id"]

        is_path = False
        actual_sink = sink
        if isinstance(sink, (str, bytes, _os.PathLike)):
            is_path = True
            actual_sink = _FileSink(_os.fspath(sink))
        handler = _Handler(id=hid, sink=actual_sink, levelno=level_obj.no, fmt=format, flt=filter, is_path=is_path)
        self._core["handlers"].append(handler)
        return hid

    def remove(self, handler_id=None):
        if handler_id is None:
            for h in list(self._core["handlers"]):
                h.close()
            self._core["handlers"].clear()
            return
        for i, h in enumerate(self._core["handlers"]):
            if h.id == handler_id:
                h.close()
                del self._core["handlers"][i]
                return
        raise ValueError(f"There is no existing handler with id {handler_id}")

    def configure(self, *, handlers=None, levels=None, extra=None, activation=None):
        if handlers is not None:
            self.remove()
            for h in handlers:
                self.add(**h)
        if extra is not None:
            self._core["extra"] = dict(extra)

    def bind(self, **extra):
        merged = dict(self._extra)
        merged.update(extra)
        return Logger(_extra=merged, _options=self._options, _core=self._core)

    def opt(
        self,
        *,
        exception=None,
        record=False,
        lazy=False,
        colors=False,
        raw=False,
        capture=True,
        depth=0,
        ansi=False,
    ):
        opts = dict(self._options)
        opts.update(
            {
                "exception": exception,
                "record": record,
                "lazy": lazy,
                "raw": raw,
                "depth": depth,
            }
        )
        return Logger(_extra=self._extra, _options=opts, _core=self._core)

    def enable(self, name):
        self._core["disabled_prefixes"].discard(name)

    def disable(self, name):
        self._core["disabled_prefixes"].add(name)

    def level(self, name):
        lvl = _resolve_level(name)
        return {"name": lvl.name, "no": lvl.no, "icon": lvl.icon}

    def log(self, level, message, *args, **kwargs):
        lvl = _resolve_level(level)
        self._log(lvl, message, args, kwargs)

    def debug(self, message, *args, **kwargs):
        self._log(_LEVELS_BY_NAME["DEBUG"], message, args, kwargs)

    def info(self, message, *args, **kwargs):
        self._log(_LEVELS_BY_NAME["INFO"], message, args, kwargs)

    def warning(self, message, *args, **kwargs):
        self._log(_LEVELS_BY_NAME["WARNING"], message, args, kwargs)

    def error(self, message, *args, **kwargs):
        self._log(_LEVELS_BY_NAME["ERROR"], message, args, kwargs)

    def exception(self, message, *args, **kwargs):
        self.opt(exception=True).error(message, *args, **kwargs)

    # --- internals ---

    def _format_message(self, message, args, kwargs, lazy: bool):
        if lazy and callable(message):
            message = message()
        if not isinstance(message, str):
            message = str(message)

        # emulate Loguru's "{}" style: replace bare "{}" with indexed placeholders
        if args:
            out = []
            idx = 0
            i = 0
            while i < len(message):
                j = message.find("{}", i)
                if j == -1:
                    out.append(message[i:])
                    break
                out.append(message[i:j])
                out.append("{" + str(idx) + "}")
                idx += 1
                i = j + 2
            message = "".join(out)

        if args or kwargs:
            try:
                message = message.format(*args, **kwargs)
            except Exception:
                message = str(message)
        return message

    def _get_frame(self, depth: int):
        """
        Return a frame corresponding to user code.

        We want opt(depth=0) called on a logging method (info/debug/...) to
        point to the direct caller of that method.

        Stack (approx):
            user -> Logger.info -> Logger._log -> Logger._get_frame

        So we need to skip:
            _get_frame (current)
            _log
            info/debug/...
        That's 3 frames from current => sys._getframe(3).
        Then apply user-provided depth on top.
        """
        base = 3
        try:
            return _sys._getframe(base + int(depth))
        except Exception:
            return _sys._getframe(0)

    def _exception_from_opt(self, opt_exc):
        if opt_exc is True:
            etype, evalue, etb = _sys.exc_info()
            if etype is None:
                return None
            return (etype, evalue, etb)
        if opt_exc in (None, False):
            return None
        if isinstance(opt_exc, BaseException):
            return (type(opt_exc), opt_exc, opt_exc.__traceback__)
        if isinstance(opt_exc, tuple) and len(opt_exc) == 3:
            return opt_exc
        return None

    def _format_exception(self, exc_tuple):
        if not exc_tuple:
            return ""
        etype, evalue, etb = exc_tuple
        return "".join(_traceback.format_exception(etype, evalue, etb))

    def _passes_activation(self, name: str):
        for prefix in self._core["disabled_prefixes"]:
            if name.startswith(prefix):
                return False
        return True

    def _check_filter(self, flt, record: dict):
        if flt is None:
            return True
        if isinstance(flt, str):
            return record.get("name", "").startswith(flt)
        if callable(flt):
            return bool(flt(record))
        if isinstance(flt, dict):
            # minimal: dict name->minlevel
            nm = record.get("name", "")
            for k, v in flt.items():
                if nm.startswith(k):
                    try:
                        minlvl = _resolve_level(v).no
                    except Exception:
                        minlvl = int(v)
                    return record["level"].no >= minlvl
            return True
        return True

    def _emit_to_sink(self, handler: _Handler, msg_obj: Message):
        sink = handler.sink
        if callable(sink) and not hasattr(sink, "write"):
            sink(msg_obj)
            return
        if hasattr(sink, "write"):
            sink.write(str(msg_obj))
            if hasattr(sink, "flush"):
                try:
                    sink.flush()
                except Exception:
                    pass
            return
        # fallback: try call
        sink(str(msg_obj))

    def _log(self, level: Level, message, args, kwargs):
        handlers = self._core["handlers"]
        if not handlers:
            return

        # fast-path: if no handler accepts this level, avoid building record
        if all(level.no < h.levelno or not h.enabled for h in handlers):
            return

        opt = self._options
        depth = int(opt.get("depth") or 0)

        frame = self._get_frame(depth)
        glb = frame.f_globals if frame is not None else {}
        name = glb.get("__name__", "")
        if not self._passes_activation(name):
            return

        extra = dict(self._core.get("extra", {}))
        extra.update(self._extra)
        call_extra = kwargs.pop("extra", None)
        if isinstance(call_extra, dict):
            extra.update(call_extra)

        lazy = bool(opt.get("lazy", False))
        msg = self._format_message(message, args, kwargs, lazy=lazy)

        now = _datetime.datetime.now()
        file_path = frame.f_code.co_filename if frame is not None else ""
        file_name = _os.path.basename(file_path) if file_path else ""
        function = frame.f_code.co_name if frame is not None else ""
        line = frame.f_lineno if frame is not None else 0

        th = _threading.current_thread()
        record = {
            "time": now,
            "level": level,
            "message": msg,
            "extra": extra,
            "name": name,
            "function": function,
            "line": line,
            "file": {"name": file_name, "path": file_path},
            "thread": {"id": getattr(th, "ident", None), "name": th.name},
            "process": {"id": _os.getpid(), "name": ""},
            "exception": None,
        }

        exc_tuple = self._exception_from_opt(opt.get("exception", None))
        if exc_tuple:
            record["exception"] = exc_tuple

        raw = bool(opt.get("raw", False))

        for h in list(handlers):
            if not h.enabled:
                continue
            if level.no < h.levelno:
                continue
            if not self._check_filter(h.flt, record):
                continue

            if raw:
                text = msg
                msg_obj = Message(text, record)
            else:
                mapping = {
                    "time": _TimeWrapper(record["time"]),
                    "level": level.name,
                    "message": record["message"],
                    "name": record["name"],
                    "function": record["function"],
                    "line": record["line"],
                    "file": _wrap(record["file"]),
                    "thread": _wrap(record["thread"]),
                    "process": _wrap(record["process"]),
                    "extra": _wrap(record["extra"]),
                    "exception": self._format_exception(record["exception"]),
                }
                try:
                    text = h.fmt.format_map(mapping)
                except KeyError:
                    # propagate to match typical Loguru behavior
                    raise
                msg_obj = Message(text, record)

            self._emit_to_sink(h, msg_obj)