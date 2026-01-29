import sys
import os
import datetime
import inspect
import threading
import traceback
import collections
from functools import partial
from copy import copy

# --- Auxiliaries ---

class Level:
    def __init__(self, name, no, color, icon):
        self.name = name
        self.no = no
        self.color = color
        self.icon = icon

    def __repr__(self):
        return f"<Level {self.name}>"

    def __str__(self):
        return self.name

    def __lt__(self, other):
        return self.no < other.no

    def __le__(self, other):
        return self.no <= other.no

    def __eq__(self, other):
        return self.no == other.no

    def __ge__(self, other):
        return self.no >= other.no

    def __gt__(self, other):
        return self.no > other.no

class Message(str):
    __slots__ = ("record",)

def get_frame(depth):
    try:
        return sys._getframe(depth)
    except ValueError:
        return None

# --- Core Logic ---

class Handler:
    def __init__(self, sink, level, format_, filter_, colorize, serialize, backtrace, diagnose, catch, enqueue):
        self.sink = sink
        self.level = level
        self.format = format_
        self.filter = filter_
        self.colorize = colorize
        self.serialize = serialize
        self.backtrace = backtrace
        self.diagnose = diagnose
        self.catch = catch
        self.enqueue = enqueue
        self.lock = threading.RLock()

        self._is_file = False
        self._is_path = False
        self._is_callable = False

        if isinstance(sink, (str, os.PathLike)):
            self._is_path = True
            self._file_handle = open(str(sink), "a", encoding="utf-8", buffering=1)
        elif hasattr(sink, "write") and callable(sink.write):
            self._is_file = True
        elif callable(sink):
            self._is_callable = True

    def emit(self, record, level_no):
        if level_no < self.level:
            return

        if self.filter is not None:
            if callable(self.filter):
                if not self.filter(record):
                    return
            elif isinstance(self.filter, str):
                if record["name"] != self.filter and not record["name"].startswith(self.filter + "."):
                    return
            elif isinstance(self.filter, dict):
                # Simplified dict filter
                pass

        # Formatting
        try:
            formatted = self.format.format_map(record)
        except Exception:
            # Fallback for formatting errors
            formatted = f"{record['time']} | {record['level']} | {record['message']}\n"

        # Add exception traceback if present
        if record["exception"]:
            exc = record["exception"]
            # Simplified traceback formatting
            tb_str = "".join(traceback.format_exception(exc.type, exc.value, exc.traceback))
            formatted += "\n" + tb_str

        # Create Message object
        msg_obj = Message(formatted)
        msg_obj.record = record

        with self.lock:
            if self._is_path:
                self._file_handle.write(formatted)
                self._file_handle.flush()
            elif self._is_file:
                self.sink.write(formatted)
                if hasattr(self.sink, "flush"):
                    self.sink.flush()
            elif self._is_callable:
                # Loguru sinks that are callables receive the Message object (str subclass)
                self.sink(msg_obj)

    def stop(self):
        if self._is_path and self._file_handle:
            self._file_handle.close()

class Core:
    def __init__(self):
        self.handlers = {}
        self.handler_count = 0
        self.levels = {
            "TRACE": Level("TRACE", 5, "", "✏️"),
            "DEBUG": Level("DEBUG", 10, "", "🐞"),
            "INFO": Level("INFO", 20, "", "ℹ️"),
            "SUCCESS": Level("SUCCESS", 25, "", "✅"),
            "WARNING": Level("WARNING", 30, "", "⚠️"),
            "ERROR": Level("ERROR", 40, "", "❌"),
            "CRITICAL": Level("CRITICAL", 50, "", "☠️"),
        }
        self.lock = threading.RLock()

    def add(self, sink, level="DEBUG", format="{time} | {level} | {message}", filter=None, colorize=None, serialize=False, backtrace=True, diagnose=True, catch=True, enqueue=False, **kwargs):
        with self.lock:
            hid = self.handler_count
            self.handler_count += 1

            # Resolve Level
            if isinstance(level, str):
                level_no = self.levels.get(level, self.levels["DEBUG"]).no
            else:
                level_no = level

            # Normalize format
            if not format.endswith("\n") and not format.endswith("\r") and not format.endswith("\r\n"):
                format += "\n"

            handler = Handler(sink, level_no, format, filter, colorize, serialize, backtrace, diagnose, catch, enqueue)
            self.handlers[hid] = handler
            return hid

    def remove(self, handler_id=None):
        with self.lock:
            if handler_id is None:
                # Remove all
                for h in self.handlers.values():
                    h.stop()
                self.handlers.clear()
            elif handler_id in self.handlers:
                self.handlers[handler_id].stop()
                del self.handlers[handler_id]

# --- Logger ---

class Logger:
    def __init__(self, core=None, extra=None, options=None):
        self._core = core if core else Core()
        self._extra = extra if extra else {}
        self._options = options if options else {
            "exception": None,
            "record": False,
            "lazy": False,
            "colors": False,
            "raw": False,
            "depth": 0,
            "capture": True
        }
        
        # If this is the root logger initialization, add default stderr sink
        if core is None:
            self.add(sys.stderr)

    def add(self, sink, **kwargs):
        return self._core.add(sink, **kwargs)

    def remove(self, handler_id=None):
        self._core.remove(handler_id)

    def bind(self, **kwargs):
        new_extra = self._extra.copy()
        new_extra.update(kwargs)
        return Logger(self._core, new_extra, self._options)

    def opt(self, *, exception=None, record=False, lazy=False, colors=False, raw=False, capture=True, depth=0):
        new_options = self._options.copy()
        if exception is not None: new_options["exception"] = exception
        if record is not False: new_options["record"] = record
        if lazy is not False: new_options["lazy"] = lazy
        if colors is not False: new_options["colors"] = colors
        if raw is not False: new_options["raw"] = raw
        if capture is not True: new_options["capture"] = capture
        if depth != 0: new_options["depth"] = depth
        return Logger(self._core, self._extra, new_options)

    def _log(self, level_name, level_no, message, args, kwargs):
        # 1. Prepare Timestamp
        now = datetime.datetime.now()

        # 2. Capture Frame
        depth = self._options["depth"] + 1 # +1 for this _log frame
        # We need to skip Logger methods. 
        # Stack: _log -> info/debug -> caller. So usually +2 frames up from here.
        # However, if opt(depth=x) is used, we adjust.
        frame = get_frame(depth + 2) 
        
        file_name = os.path.basename(frame.f_code.co_filename) if frame else "unknown"
        file_path = frame.f_code.co_filename if frame else "unknown"
        line_no = frame.f_lineno if frame else 0
        func_name = frame.f_code.co_name if frame else "unknown"
        module_name = frame.f_globals.get("__name__", "unknown") if frame else "unknown"
        
        # 3. Handle Exception
        exception_record = None
        if self._options["exception"]:
            exc_info = sys.exc_info()
            if exc_info[0] is not None:
                # Create a simple object to hold exception info
                RecordException = collections.namedtuple("RecordException", ["type", "value", "traceback"])
                exception_record = RecordException(*exc_info)

        # 4. Format Message
        if self._options["lazy"]:
            # If lazy, args are functions
            args = [arg() if callable(arg) else arg for arg in args]
            kwargs = {k: (v() if callable(v) else v) for k, v in kwargs.items()}

        if args or kwargs:
            try:
                # Loguru supports .format() style by default
                formatted_message = message.format(*args, **kwargs)
            except Exception:
                # Fallback or legacy % formatting if format fails (simplified)
                try:
                    formatted_message = message % args
                except:
                    formatted_message = message
        else:
            formatted_message = message

        # 5. Construct Record
        level_obj = self._core.levels.get(level_name, Level(level_name, level_no, "", ""))
        
        record = {
            "elapsed": datetime.timedelta(0), # Stub
            "exception": exception_record,
            "extra": self._extra,
            "file": collections.namedtuple("File", ["name", "path"])(file_name, file_path),
            "function": func_name,
            "level": level_obj,
            "line": line_no,
            "message": formatted_message,
            "module": module_name,
            "name": module_name,
            "process": os.getpid(),
            "thread": threading.get_ident(),
            "time": now,
        }

        # 6. Emit to Handlers
        for handler in self._core.handlers.values():
            handler.emit(record, level_no)

    def trace(self, message, *args, **kwargs):
        self._log("TRACE", 5, message, args, kwargs)

    def debug(self, message, *args, **kwargs):
        self._log("DEBUG", 10, message, args, kwargs)

    def info(self, message, *args, **kwargs):
        self._log("INFO", 20, message, args, kwargs)

    def success(self, message, *args, **kwargs):
        self._log("SUCCESS", 25, message, args, kwargs)

    def warning(self, message, *args, **kwargs):
        self._log("WARNING", 30, message, args, kwargs)

    def error(self, message, *args, **kwargs):
        self._log("ERROR", 40, message, args, kwargs)

    def critical(self, message, *args, **kwargs):
        self._log("CRITICAL", 50, message, args, kwargs)

    def exception(self, message, *args, **kwargs):
        # Automatically enable exception capturing
        opts = self._options.copy()
        opts["exception"] = True
        # Create temporary logger with exception enabled
        temp_logger = Logger(self._core, self._extra, opts)
        temp_logger.error(message, *args, **kwargs)

    def log(self, level, message, *args, **kwargs):
        if isinstance(level, int):
            level_no = level
            level_name = f"Level {level}"
            # Try to find existing name
            for name, lvl in self._core.levels.items():
                if lvl.no == level:
                    level_name = name
                    break
        else:
            level_name = level
            level_no = self._core.levels.get(level, self._core.levels["DEBUG"]).no
            
        self._log(level_name, level_no, message, args, kwargs)

    def level(self, name, no=None, color=None, icon=None):
        if no is not None:
            self._core.levels[name] = Level(name, no, color or "", icon or "")
        return self._core.levels.get(name)