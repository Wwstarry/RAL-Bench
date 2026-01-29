import sys
import os
import datetime
import traceback
import inspect
import threading

# Simple level mapping for demonstration
LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
}

class _Logger:
    _lock = threading.Lock()
    _next_sink_id = 1

    def __init__(self, sinks=None, context=None, options=None):
        # Each sink is stored as a dict:
        # {
        #   "id": int,
        #   "sink": func_or_fileobj,
        #   "level": int,
        #   "active": bool,
        #   "is_file": bool,
        #   "format": str (if needed),
        # }
        self._sinks = sinks if sinks is not None else {}
        # Bind context
        self._context = context if context is not None else {}
        # Stores ephemeral options from .opt(...)
        self._options = options if options is not None else {}

    def add(self, sink, level="DEBUG", format=None):
        """
        Add a new logging sink.
        `sink` can be:
         - a callable taking a single string argument
         - a string file path to write to
        """
        with self._lock:
            sink_id = self._next_sink_id
            self._next_sink_id += 1

            level_no = LEVELS.get(level.upper(), 10)
            is_file = False
            sink_obj = sink
            if isinstance(sink, str):
                try:
                    sink_obj = open(sink, "a", encoding="utf-8")
                    is_file = True
                except Exception as e:
                    raise ValueError(f"Could not open file {sink}: {e}")

            self._sinks[sink_id] = {
                "id": sink_id,
                "sink": sink_obj,
                "level": level_no,
                "active": True,
                "is_file": is_file,
                "format": format,
            }
        return sink_id

    def remove(self, sink_id=None):
        """
        Remove a sink by its id or remove all if sink_id is None.
        """
        with self._lock:
            if sink_id is None:
                # Remove all
                keys = list(self._sinks.keys())
                for k in keys:
                    s = self._sinks.pop(k)
                    if s["is_file"]:
                        try:
                            s["sink"].close()
                        except:
                            pass
            else:
                s = self._sinks.pop(sink_id, None)
                if s and s["is_file"]:
                    try:
                        s["sink"].close()
                    except:
                        pass

    def bind(self, **kwargs):
        """
        Return a new logger with additional context bound.
        """
        new_context = self._context.copy()
        new_context.update(kwargs)
        return _Logger(self._sinks, new_context, self._options)

    def opt(self, **kwargs):
        """
        Return a new logger with ephemeral options.
        Typical use is "exception=True".
        """
        new_options = self._options.copy()
        new_options.update(kwargs)
        return _Logger(self._sinks, self._context, new_options)

    def debug(self, message, *args, **kwargs):
        self._log("DEBUG", message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self._log("INFO", message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self._log("WARNING", message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self._log("ERROR", message, *args, **kwargs)

    def _log(self, level_name, message, *args, **kwargs):
        """
        Internal logging method. Calls all sinks of sufficient level.
        """
        # Check ephemeral 'exception=True', etc.
        exc_opt = self._options.get("exception", False)

        # If the message includes format placeholders, apply them
        if args or kwargs:
            try:
                message = message.format(*args, **kwargs)
            except:
                # If formatting fails, fallback to original message
                pass

        # Prepare the log record data
        record = self._make_log_record(level_name, message)

        # If exc_opt is True, attach current exception traceback if any
        if exc_opt:
            exc_info = sys.exc_info()
            if exc_info and exc_info[0] is not None:
                error_str = "".join(traceback.format_exception(*exc_info))
                record["exception"] = error_str

        self._emit(record)
        # Reset ephemeral options after a log call
        self._options = {}

    def _make_log_record(self, level_name, message):
        now = datetime.datetime.now()
        time_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Attempt to figure out calling frame
        frame = inspect.stack()[3]
        filename = os.path.basename(frame.filename)
        lineno = frame.lineno

        # Build record
        record = {
            "time": time_str,
            "level": level_name,
            "file": filename,
            "line": lineno,
            "message": message,
            "context": self._context.copy(),
            "exception": None,
        }
        return record

    def _emit(self, record):
        with self._lock:
            for sink_id, sink_info in self._sinks.items():
                if not sink_info["active"]:
                    continue
                if LEVELS.get(record["level"], 10) < sink_info["level"]:
                    continue

                out = self._format_message(record, sink_info["format"])
                try:
                    if sink_info["is_file"]:
                        sink_info["sink"].write(out)
                        sink_info["sink"].flush()
                    else:
                        sink_info["sink"](out)
                except Exception:
                    # We silently ignore sink failures for simplicity
                    pass

    def _format_message(self, record, custom_format):
        """
        Build a textual representation of the log record,
        including optional custom_format use.
        """
        # If a custom format is provided, attempt to use it
        if custom_format:
            try:
                msg = custom_format.format(**record)
            except:
                # fallback 
                msg = self._default_format(record)
        else:
            msg = self._default_format(record)
        return msg

    def _default_format(self, record):
        # Default log message structure
        # Time | Level | file:line - message + context + optional exception
        base = "{time} | {level} | {file}:{line} - {message}".format(**record)
        if record["context"]:
            # Append context in "key=value" pairs
            ctx = " ".join(f"{k}={v}" for k, v in record["context"].items())
            base += f" | {ctx}"
        if record["exception"]:
            # Attach the traceback
            base += "\n" + record["exception"].rstrip("\n") + "\n"
        else:
            base += "\n"
        return base

# Instantiate a global logger object as done by loguru
logger = _Logger()