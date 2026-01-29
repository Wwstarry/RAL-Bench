import sys
import threading
import datetime
import inspect
import traceback
import re
from collections import namedtuple

# --- Levels ---
Level = namedtuple("Level", "name no icon")

LEVELS = {
    "DEBUG": Level("DEBUG", 10, "🐞"),
    "INFO": Level("INFO", 20, "ℹ️"),
    "SUCCESS": Level("SUCCESS", 25, "✔️"),
    "WARNING": Level("WARNING", 30, "⚠️"),
    "ERROR": Level("ERROR", 40, "❌"),
    "CRITICAL": Level("CRITICAL", 50, "🔥"),
}

# --- Formatter ---

class Formatter:
    def __init__(self, format_string):
        # Strip color tags for compatibility with non-tty outputs
        self._format_string = re.sub(r"</?([a-zA-Z0-9_]+)>", "", format_string)

    def format(self, record):
        def replacer(match):
            tag = match.group(1)
            parts = tag.rsplit(":", 1)
            key = parts[0].strip()
            fmt = parts[1].strip() if len(parts) > 1 else ""

            if key == "message":
                return str(record["message"])
            if key == "level":
                return ("{:" + fmt + "}").format(record["level"].name)
            if key == "time":
                time_str = self._format_time(record["time"], fmt)
                return time_str
            if key == "name":
                return str(record["name"])
            if key == "file":
                return str(record["file"].name)
            if key == "line":
                return str(record["line"])
            if key == "function":
                return str(record["function"])
            if key.startswith("extra"):
                if key == "extra":
                    return str(record["extra"])
                m = re.match(r"extra\[(.+)\]", key)
                if m:
                    extra_key = m.group(1).strip("'\"")
                    return str(record["extra"].get(extra_key, ""))
            if key == "exception":
                if record.get("exception"):
                    exc_text = record["exception"]
                    record["exception"] = None  # Consume it
                    return exc_text
                return ""
            return match.group(0)

        return re.sub(r"\{(.+?)\}", replacer, self._format_string)

    def _format_time(self, time_obj, fmt):
        if not fmt:
            fmt = "YYYY-MM-DD HH:mm:ss.SSS"

        # Replace Loguru-specific tokens with strftime equivalents
        fmt = fmt.replace("YYYY", "%Y").replace("YY", "%y")
        fmt = fmt.replace("MM", "%m").replace("M", "%-m")
        fmt = fmt.replace("DD", "%d").replace("D", "%-d")
        fmt = fmt.replace("HH", "%H").replace("H", "%-H")
        fmt = fmt.replace("mm", "%M").replace("m", "%-M")
        fmt = fmt.replace("ss", "%S").replace("s", "%-S")
        
        # Handle milliseconds (SSS) and microseconds (f)
        if "SSS" in fmt:
            ms = f"{time_obj.microsecond // 1000:03d}"
            fmt = fmt.replace("SSS", ms)
        if "f" in fmt:
            fmt = fmt.replace("f", str(time_obj.microsecond))

        return time_obj.strftime(fmt)

# --- Sink ---

class Sink:
    def __init__(self, writer, level, formatter, filter_):
        self._writer = writer
        self._levelno = level
        self._formatter = formatter
        self._filter = filter_
        self._is_file = hasattr(writer, 'close') and hasattr(writer, 'flush')

    def write(self, record):
        if record["level"].no < self._levelno:
            return
        
        if self._filter and not self._filter(record):
            return

        formatted_message = self._formatter.format(record)
        
        if not formatted_message.endswith('\n'):
            formatted_message += '\n'
            
        self._writer.write(formatted_message)
        
        if record.get("exception"):
            self._writer.write(record["exception"])
        
        if self._is_file:
            self._writer.flush()

    def stop(self):
        if self._is_file and not self._writer.closed:
            self._writer.close()

# --- Logger ---

class Logger:
    def __init__(self, parent=None, context=None, options=None):
        if parent:
            self._sinks = parent._sinks
            self._lock = parent._lock
            self._level_name_to_no = parent._level_name_to_no
            self._next_id_obj = parent._next_id_obj
        else:
            self._sinks = {}
            self._lock = threading.Lock()
            self._level_name_to_no = LEVELS
            self._next_id_obj = [0]  # Mutable integer in a list

        self._context = context if context is not None else {}
        self._options = options if options is not None else {}

        for level_name in self._level_name_to_no:
            self._make_level_method(level_name.lower())

    def _make_level_method(self, name):
        if not hasattr(self, name):
            def log_method(message, *args, **kwargs):
                self._log(name.upper(), message, *args, **kwargs)
            setattr(self, name, log_method)

    def _get_next_id(self):
        with self._lock:
            current_id = self._next_id_obj[0]
            self._next_id_obj[0] += 1
            return current_id

    def add(self, sink, *, level="DEBUG", format="{message}\n", filter=None, **kwargs):
        level_no = self._level_name_to_no[level].no if isinstance(level, str) else level
        
        writer = None
        if isinstance(sink, str):
            writer = open(sink, "a", encoding="utf-8")
        elif hasattr(sink, 'write'):
            writer = sink
        elif callable(sink):
            # For callable sinks, the writer is a wrapper
            writer = lambda msg: sink(msg)

        if writer is None:
            raise ValueError("Invalid sink specified")

        formatter = Formatter(format)
        new_sink = Sink(writer, level_no, formatter, filter)
        
        sink_id = self._get_next_id()
        with self._lock:
            self._sinks[sink_id] = new_sink
        
        return sink_id

    def remove(self, handler_id=None):
        with self._lock:
            if handler_id is None:
                for sid in list(self._sinks.keys()):
                    self._sinks.pop(sid).stop()
                return

            if handler_id in self._sinks:
                self._sinks.pop(handler_id).stop()
            else:
                raise ValueError(f"Sink {handler_id} does not exist.")

    def bind(self, **kwargs):
        new_context = self._context.copy()
        new_context.update(kwargs)
        return Logger(parent=self, context=new_context, options=self._options.copy())

    def opt(self, **kwargs):
        new_options = self._options.copy()
        new_options.update(kwargs)
        return Logger(parent=self, context=self._context.copy(), options=new_options)

    def _log(self, level_name, message, *args, **kwargs):
        level = self._level_name_to_no[level_name]
        
        # Find caller frame
        frame = inspect.currentframe()
        depth = self._options.get("depth", 0)
        i = 0
        while frame:
            if frame.f_code.co_filename != __file__:
                if i == depth:
                    break
                i += 1
            frame = frame.f_back
        
        if not frame:
            frame = inspect.currentframe()

        # Format message
        try:
            formatted_message = message.format(*args, **kwargs)
        except Exception:
            formatted_message = message

        # Handle exception
        exc_info = self._options.get("exception")
        exc_text = None
        if exc_info:
            if isinstance(exc_info, bool):
                exc_info = sys.exc_info()
            elif isinstance(exc_info, BaseException):
                exc_info = (type(exc_info), exc_info, exc_info.__traceback__)

            if exc_info and exc_info[0] is not None:
                exc_text = "".join(traceback.format_exception(*exc_info))

        File = namedtuple("File", "name path")
        record = {
            "message": formatted_message,
            "level": level,
            "time": datetime.datetime.now(),
            "extra": self._context.copy(),
            "exception": exc_text,
            "name": frame.f_globals.get("__name__"),
            "file": File(frame.f_code.co_filename.split("/")[-1], frame.f_code.co_filename),
            "line": frame.f_lineno,
            "function": frame.f_code.co_name,
        }
        
        with self._lock:
            if not self._sinks:
                return

            for sink in self._sinks.values():
                sink.write(record.copy())