import sys
import os
import io
import datetime
import traceback
import threading
import inspect
import functools
import contextvars
import re
from types import FrameType
from typing import Any, Callable, Dict, List, Optional, TextIO, Tuple, Type, Union, cast

# Context variable to store the current context
_context_var = contextvars.ContextVar("loguru_context", default={})

class _RecordLevel:
    """Level information for a record."""
    __slots__ = ("name", "no", "icon")
    
    def __init__(self, name: str, no: int, icon: str = ""):
        self.name = name
        self.no = no
        self.icon = icon

class _Levels:
    """Loguru levels."""
    TRACE = _RecordLevel("TRACE", 5, "🔍")
    DEBUG = _RecordLevel("DEBUG", 10, "🐛")
    INFO = _RecordLevel("INFO", 20, "ℹ️")
    SUCCESS = _RecordLevel("SUCCESS", 25, "✅")
    WARNING = _RecordLevel("WARNING", 30, "⚠️")
    ERROR = _RecordLevel("ERROR", 40, "❌")
    CRITICAL = _RecordLevel("CRITICAL", 50, "💀")
    
    _by_name = {
        "TRACE": TRACE,
        "DEBUG": DEBUG,
        "INFO": INFO,
        "SUCCESS": SUCCESS,
        "WARNING": WARNING,
        "ERROR": ERROR,
        "CRITICAL": CRITICAL,
    }
    
    _by_no = {
        5: TRACE,
        10: DEBUG,
        20: INFO,
        25: SUCCESS,
        30: WARNING,
        40: ERROR,
        50: CRITICAL,
    }
    
    @classmethod
    def get_level(cls, name_or_no: Union[str, int]) -> _RecordLevel:
        if isinstance(name_or_no, str):
            return cls._by_name.get(name_or_no.upper(), cls.INFO)
        else:
            return cls._by_no.get(name_or_no, cls.INFO)

class _Message:
    """Class representing a log message with all its context."""
    __slots__ = ("record", "exception")
    
    def __init__(self, record: Dict[str, Any], exception: Optional[Dict[str, Any]] = None):
        self.record = record
        self.exception = exception

class _Handler:
    """Handler managing a logging sink."""
    __slots__ = ("sink", "level", "format", "filter", "file_handle", "id")
    
    def __init__(self, 
                 sink: Union[TextIO, str, Callable[[Dict[str, Any]], None]], 
                 level: Union[str, int],
                 format_: str,
                 filter_: Optional[Callable[[Dict[str, Any]], bool]],
                 id_: int):
        self.sink = sink
        self.level = _Levels.get_level(level).no if level is not None else 0
        self.format = format_
        self.filter = filter_
        self.file_handle = None
        self.id = id_
        
        # If sink is a string, it's a file path
        if isinstance(sink, str):
            self.file_handle = open(sink, "a", encoding="utf8")
            self.sink = self.file_handle
    
    def emit(self, message: _Message) -> None:
        """Emit a message to the sink."""
        if message.record["level"].no < self.level:
            return
        
        if self.filter and not self.filter(message.record):
            return
        
        formatted = self._format_message(message)
        
        if isinstance(self.sink, io.TextIOBase) or hasattr(self.sink, "write"):
            sink = cast(TextIO, self.sink)
            sink.write(formatted + "\n")
            sink.flush()
        elif callable(self.sink):
            sink_func = cast(Callable[[Dict[str, Any]], None], self.sink)
            sink_func(message.record)
    
    def _format_message(self, message: _Message) -> str:
        """Format the message according to format string."""
        result = self.format
        
        for key, value in message.record.items():
            if isinstance(value, datetime.datetime):
                value = value.strftime("%Y-%m-%d %H:%M:%S.%f")
            if key == "level":
                value = value.name
            
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value))
        
        # Handle exception if present
        if message.exception:
            result += "\n" + message.exception["traceback"]
        
        return result
    
    def close(self) -> None:
        """Close the handler."""
        if self.file_handle:
            self.file_handle.close()

class _ContextualizedLogger:
    """A logger with bound context."""
    __slots__ = ("_parent", "_context", "_options")
    
    def __init__(self, parent: "Logger", context: Dict[str, Any], options: Dict[str, Any]):
        self._parent = parent
        self._context = context
        self._options = options
    
    def debug(self, __message: str, *args, **kwargs) -> None:
        self._parent._log(_Levels.DEBUG, __message, args, kwargs, self._context, self._options)
    
    def info(self, __message: str, *args, **kwargs) -> None:
        self._parent._log(_Levels.INFO, __message, args, kwargs, self._context, self._options)
    
    def warning(self, __message: str, *args, **kwargs) -> None:
        self._parent._log(_Levels.WARNING, __message, args, kwargs, self._context, self._options)
    
    def error(self, __message: str, *args, **kwargs) -> None:
        self._parent._log(_Levels.ERROR, __message, args, kwargs, self._context, self._options)
    
    def critical(self, __message: str, *args, **kwargs) -> None:
        self._parent._log(_Levels.CRITICAL, __message, args, kwargs, self._context, self._options)
    
    def exception(self, __message: str, *args, **kwargs) -> None:
        self._parent._log(_Levels.ERROR, __message, args, kwargs, self._context, self._options, True)
    
    def bind(self, **kwargs) -> "_ContextualizedLogger":
        new_context = self._context.copy()
        new_context.update(kwargs)
        return _ContextualizedLogger(self._parent, new_context, self._options)
    
    def opt(self, *, depth: int = 0, exception: Optional[bool] = None, 
            record: bool = False, lazy: bool = False) -> "_ContextualizedLogger":
        new_options = self._options.copy()
        if depth != 0:
            new_options["depth"] = depth
        if exception is not None:
            new_options["exception"] = exception
        if record:
            new_options["record"] = record
        if lazy:
            new_options["lazy"] = lazy
        return _ContextualizedLogger(self._parent, self._context, new_options)

class Logger:
    """The main logger class, implementing Loguru-like API."""
    __slots__ = ("_handlers", "_handler_id", "_default_format")
    
    def __init__(self):
        self._handlers: Dict[int, _Handler] = {}
        self._handler_id = 0
        self._default_format = "{time} | {level} | {message}"
    
    def add(self, 
            sink: Union[TextIO, str, Callable[[Dict[str, Any]], None]], 
            level: Union[str, int] = "DEBUG",
            format: str = None,
            filter: Optional[Callable[[Dict[str, Any]], bool]] = None) -> int:
        """Add a new sink to the logger."""
        handler_id = self._handler_id
        self._handler_id += 1
        
        format_str = format or self._default_format
        
        self._handlers[handler_id] = _Handler(
            sink=sink,
            level=level,
            format_=format_str,
            filter_=filter,
            id_=handler_id
        )
        
        return handler_id
    
    def remove(self, handler_id: Optional[int] = None) -> None:
        """Remove a sink from the logger."""
        if handler_id is None:
            # Remove all handlers
            for h_id in list(self._handlers.keys()):
                self._handlers[h_id].close()
                del self._handlers[h_id]
        elif handler_id in self._handlers:
            self._handlers[handler_id].close()
            del self._handlers[handler_id]
    
    def _log(self, 
             level: _RecordLevel, 
             message: str, 
             args: Tuple[Any, ...], 
             kwargs: Dict[str, Any],
             context: Dict[str, Any] = None,
             options: Dict[str, Any] = None,
             with_exception: bool = False) -> None:
        """Core logging method."""
        # Format the message with args if any
        if args:
            try:
                message = message.format(*args)
            except Exception as e:
                message = f"Error formatting message: {message}, {e}"
        
        # Prepare record context
        record_context = {}
        if context:
            record_context.update(context)
        if "extra" in kwargs:
            record_context.update(kwargs["extra"])
        
        # Create the record
        now = datetime.datetime.now()
        frame = self._get_caller_frame(options.get("depth", 0) if options else 0)
        
        record = {
            "time": now,
            "level": level,
            "message": message,
            "file": frame.f_code.co_filename if frame else "?",
            "function": frame.f_code.co_name if frame else "?",
            "line": frame.f_lineno if frame else 0,
            "thread": threading.get_ident(),
            "thread_name": threading.current_thread().name,
            "process": os.getpid(),
        }
        
        # Add extra context
        record.update(record_context)
        
        # Handle exceptions
        exception_data = None
        exception_option = options.get("exception", None) if options else None
        
        if with_exception or (exception_option is True):
            exc_info = sys.exc_info()
            if exc_info[0] is not None:
                traceback_str = "".join(traceback.format_exception(*exc_info))
                exception_data = {
                    "type": exc_info[0].__name__,
                    "value": str(exc_info[1]),
                    "traceback": traceback_str
                }
        
        # Create message object
        msg = _Message(record, exception_data)
        
        # Emit to all handlers
        for handler in self._handlers.values():
            handler.emit(msg)
    
    def _get_caller_frame(self, depth_adjustment: int = 0) -> Optional[FrameType]:
        """Find the caller frame."""
        frame = inspect.currentframe()
        if not frame:
            return None
        
        # Skip frames in this file or loguru package
        depth = 1 + depth_adjustment  # Default depth + adjustment
        while frame and depth > 0:
            frame = frame.f_back
            depth -= 1
        
        while frame:
            if frame.f_code.co_filename != __file__ and 'loguru' not in frame.f_code.co_filename:
                return frame
            frame = frame.f_back
        
        return None
    
    def debug(self, __message: str, *args, **kwargs) -> None:
        """Log a debug message."""
        self._log(_Levels.DEBUG, __message, args, kwargs)
    
    def info(self, __message: str, *args, **kwargs) -> None:
        """Log an info message."""
        self._log(_Levels.INFO, __message, args, kwargs)
    
    def warning(self, __message: str, *args, **kwargs) -> None:
        """Log a warning message."""
        self._log(_Levels.WARNING, __message, args, kwargs)
    
    def error(self, __message: str, *args, **kwargs) -> None:
        """Log an error message."""
        self._log(_Levels.ERROR, __message, args, kwargs)
    
    def critical(self, __message: str, *args, **kwargs) -> None:
        """Log a critical message."""
        self._log(_Levels.CRITICAL, __message, args, kwargs)
    
    def exception(self, __message: str, *args, **kwargs) -> None:
        """Log an exception (error with traceback)."""
        self._log(_Levels.ERROR, __message, args, kwargs, with_exception=True)
    
    def bind(self, **kwargs) -> _ContextualizedLogger:
        """Bind context values to the logger."""
        return _ContextualizedLogger(self, kwargs, {})
    
    def opt(self, *, depth: int = 0, exception: Optional[bool] = None, 
            record: bool = False, lazy: bool = False) -> _ContextualizedLogger:
        """Set options for the logger."""
        options = {}
        if depth != 0:
            options["depth"] = depth
        if exception is not None:
            options["exception"] = exception
        if record:
            options["record"] = record
        if lazy:
            options["lazy"] = lazy
        return _ContextualizedLogger(self, {}, options)

# Create the global logger instance
logger = Logger()

# Add stderr as default sink
if sys.stderr:
    logger.add(sys.stderr)