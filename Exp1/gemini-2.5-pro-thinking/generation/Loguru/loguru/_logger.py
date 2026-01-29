import datetime
import inspect
import os
import re
import sys
import threading
import traceback
from collections import namedtuple

# --- Level Definition ---
Level = namedtuple("Level", ["name", "no", "color", "icon"])

# --- Sink Class ---
class Sink:
    def __init__(self, writer, level, format, filter, colorize, serialize, backtrace, diagnose, enqueue, catch):
        self.writer = writer
        self.levelno = level
        self.format = format
        self.filter = filter
        self.colorize = colorize
        self.serialize = serialize
        self.backtrace = backtrace
        self.diagnose = diagnose
        self.enqueue = enqueue
        self.catch = catch
        self._lock = threading.Lock()
        self._file = None  # To store file object for closing

    def write(self, message):
        with self._lock:
            try:
                self.writer(message)
            except Exception:
                if self.catch:
                    # Mimic Loguru's internal error reporting
                    print("--- Logging error in Loguru sink ---", file=sys.stderr)
                    traceback.print_exc(file=sys.stderr)
                    print("--- End of logging error ---", file=sys.stderr)
                else:
                    raise

    def stop(self):
        if self._file:
            self._file.close()

# --- Core Logger Logic ---
class _Core:
    def __init__(self):
        self.sinks = {}
        self._sink_id_counter = 0
        self._lock = threading.Lock()
        self._levels = {
            "TRACE": Level("TRACE", 5, "<cyan>", " "),
            "DEBUG": Level("DEBUG", 10, "<blue>", " "),
            "INFO": Level("INFO", 20, "<green>", " "),
            "SUCCESS": Level("SUCCESS", 25, "<bold><green>", " "),
            "WARNING": Level("WARNING", 30, "<yellow>", " "),
            "ERROR": Level("ERROR", 40, "<red>", " "),
            "CRITICAL": Level("CRITICAL", 50, "<bold><red>", " "),
        }
        self._level_names = {level.no: name for name, level in self._levels.items()}
        self._enabled = {}
        self.patcher = self  # Stub for patcher

        # Add default sink to stderr
        self.add(sys.stderr, level="DEBUG", format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>\n")

    def get_level_no(self, level):
        if isinstance(level, str):
            return self._levels[level.upper()].no
        return level

    def add(self, sink, level="DEBUG", format=None, filter=None, colorize=None, serialize=False, backtrace=True, diagnose=True, enqueue=False, catch=True, **kwargs):
        if format is None:
            format = "{message}\n"

        levelno = self.get_level_no(level)
        writer = sink
        file_obj = None

        if isinstance(sink, str) or hasattr(sink, "__fspath__"):
            file_obj = open(sink, "a", encoding="utf-8", newline="")
            writer = file_obj.write
        elif hasattr(sink, "write"):
            writer = sink.write
        elif callable(sink):
            writer = sink
        else:
            raise ValueError("Sink must be a file-like object, a callable, or a file path.")

        new_sink = Sink(writer, levelno, format, filter, colorize, serialize, backtrace, diagnose, enqueue, catch)
        if file_obj:
            new_sink._file = file_obj

        with self._lock:
            handler_id = self._sink_id_counter
            self._sink_id_counter += 1
            self.sinks[handler_id] = new_sink
        return handler_id

    def remove(self, handler_id=None):
        if handler_id is None:
            with self._lock:
                for sink in self.sinks.values():
                    sink.stop()
                self.sinks.clear()
            return

        with self._lock:
            if handler_id not in self.sinks:
                raise ValueError(f"Sink {handler_id} does not exist.")
            self.sinks[handler_id].stop()
            del self.sinks[handler_id]

    def _format_time(self, timestamp, fmt):
        replacements = {
            "YYYY": "%Y", "YY": "%y", "MMMM": "%B", "MMM": "%b", "MM": "%m", "DD": "%d",
            "dddd": "%A", "ddd": "%a", "d": "%w",
            "HH": "%H", "hh": "%I", "mm": "%M", "ss": "%S", "A": "%p", "a": "%p",
            "ZZ": "%z", "z": "%Z"
        }
        
        # Handle microseconds/milliseconds
        if "SSSSSS" in fmt:
            us = f"{timestamp.microsecond:06d}"
            fmt = fmt.replace("SSSSSS", us)
        elif "SSS" in fmt:
            ms = f"{timestamp.microsecond // 1000:03d}"
            fmt = fmt.replace("SSS", ms)

        for token, directive in replacements.items():
            fmt = fmt.replace(token, directive)
        
        return timestamp.strftime(fmt)

    def _format_record(self, record, sink):
        format_string = sink.format
        
        should_colorize = sink.colorize
        if should_colorize is None and hasattr(sink.writer, "isatty"):
            should_colorize = sink.writer.isatty()

        if not should_colorize:
            format_string = re.sub(r"<[a-zA-Z0-9=,;_-]*>", "", format_string)

        def replacer(match):
            tag_content = match.group(1)
            parts = tag_content.split(":", 1)
            key = parts[0].strip()
            fmt_spec = parts[1].strip() if len(parts) > 1 else ""

            value = ""
            if "." in key:
                main_key, sub_key = key.split(".", 1)
                if main_key == "extra" and sub_key in record["extra"]:
                    value = record["extra"][sub_key]
                elif main_key in record and hasattr(record[main_key], sub_key):
                    value = getattr(record[main_key], sub_key)
            elif key in record:
                value = record[key]

            if key == "time" and fmt_spec:
                return self._format_time(value, fmt_spec)
            
            if fmt_spec:
                return f"{{:{fmt_spec}}}".format(value)
            
            return str(value)

        output = re.sub(r"{(.*?)}", replacer, format_string)

        if record["exception"] and sink.backtrace:
            exc_text = "".join(traceback.format_exception(*record["exception"]))
            if output.endswith("\n"):
                output = output.rstrip("\n") + "\n" + exc_text
            else:
                output += "\n" + exc_text
        
        return output

    def log(self, level, extra, from_decorator, options, message, args, kwargs):
        level_name = level.upper()
        if level_name not in self._levels:
            return

        level_info = self._levels[level_name]

        if not any(level_info.no >= sink.levelno for sink in self.sinks.values()):
            return

        frame = inspect.currentframe()
        while frame and frame.f_code.co_filename == __file__:
            frame = frame.f_back
        
        if not frame: return

        exc_info = None
        if options.get("exception"):
            exc_info = sys.exc_info()
            if not exc_info[0]: exc_info = None

        record = {
            "elapsed": datetime.timedelta(0),
            "exception": exc_info,
            "extra": {**extra, **kwargs},
            "file": namedtuple("File", ["path", "name"])(frame.f_code.co_filename, os.path.basename(frame.f_code.co_filename)),
            "function": frame.f_code.co_name,
            "level": level_info,
            "line": frame.f_lineno,
            "message": str(message).format(*args) if args else str(message),
            "module": frame.f_globals.get("__name__"),
            "name": frame.f_globals.get("__name__"),
            "process": namedtuple("Process", ["id", "name"])(os.getpid(), "MainProcess"),
            "thread": namedtuple("Thread", ["id", "name"])(threading.get_ident(), threading.current_thread().name),
            "time": datetime.datetime.now(),
        }

        for sink in self.sinks.values():
            if level_info.no < sink.levelno:
                continue
            
            if sink.filter and not sink.filter(record):
                continue

            formatted_message = self._format_record(record, sink)
            sink.write(formatted_message)

class Logger:
    def __init__(self, core, extra, patcher=None):
        self._core = core
        self._extra = extra
        self._patcher = patcher

        for name in self._core._levels:
            self._make_level_method(name)

    def _make_level_method(self, name):
        level_name = name
        def log_method(message, *args, **kwargs):
            self._log(level_name, False, {}, message, args, kwargs)
        setattr(self, name.lower(), log_method)

    def add(self, *args, **kwargs):
        return self._core.add(*args, **kwargs)

    def remove(self, *args, **kwargs):
        self._core.remove(*args, **kwargs)

    def bind(self, **kwargs):
        new_extra = self._extra.copy()
        new_extra.update(kwargs)
        return Logger(self._core, new_extra, self._patcher)

    def opt(self, **kwargs):
        return _LoggerProxy(self, kwargs)

    def _log(self, level, from_decorator, options, message, args, kwargs):
        self._core.log(level, self._extra, from_decorator, options, message, args, kwargs)

    def patch(self, patcher):
        pass

    def disable(self, name):
        self._core._enabled[name] = False

    def enable(self, name):
        self._core._enabled[name] = True

    @property
    def catch(self):
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    self.exception("An error has been caught in function '{}'", func.__name__)
            return wrapper
        return decorator
    
    def exception(self, message, *args, **kwargs):
        kwargs['exception'] = True
        self._log("ERROR", False, {}, message, args, kwargs)

class _LoggerProxy:
    def __init__(self, logger, options):
        self._logger = logger
        self._options = options

    def __getattr__(self, name):
        if name.upper() in self._logger._core._levels:
            def log_method(message, *args, **kwargs):
                self._logger._log(name.upper(), False, self._options, message, args, kwargs)
            return log_method
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

_core = _Core()
logger = Logger(core=_core, extra={}, patcher=_core.patcher)