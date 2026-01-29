"""
Core logger implementation for Loguru.
"""

import sys
import time
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
from functools import wraps
import threading


class LogRecord:
    """Represents a single log record."""
    
    def __init__(
        self,
        name: str,
        level: int,
        level_name: str,
        message: str,
        record: Dict[str, Any],
    ):
        self.name = name
        self.level = level
        self.level_name = level_name
        self.message = message
        self.record = record


class Logger:
    """
    A pure Python logging library compatible with Loguru.
    """
    
    # Log levels
    LEVELS = {
        "TRACE": 5,
        "DEBUG": 10,
        "INFO": 20,
        "SUCCESS": 25,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
    }
    
    LEVEL_NAMES = {v: k for k, v in LEVELS.items()}
    
    def __init__(self):
        self._handlers: List[Tuple[int, Callable, Dict[str, Any]]] = []
        self._context: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._handler_id_counter = 0
        
        # Add default stderr handler
        self._default_handler_id = self.add(
            sys.stderr,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name} - {message}",
        )
    
    def add(
        self,
        sink: Any,
        *,
        format: str = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name} - {message}",
        level: str = "DEBUG",
        colorize: bool = False,
        serialize: bool = False,
        backtrace: bool = True,
        diagnose: bool = True,
        enqueue: bool = False,
        catch: bool = False,
        **kwargs
    ) -> int:
        """
        Add a new handler to the logger.
        
        Args:
            sink: File path, file object, or callable
            format: Format string for log messages
            level: Minimum log level
            colorize: Whether to colorize output
            serialize: Whether to serialize to JSON
            backtrace: Whether to include backtrace
            diagnose: Whether to include diagnostic info
            enqueue: Whether to enqueue messages
            catch: Whether to catch exceptions in handlers
            **kwargs: Additional options
        
        Returns:
            Handler ID for later removal
        """
        with self._lock:
            handler_id = self._handler_id_counter
            self._handler_id_counter += 1
            
            level_num = self.LEVELS.get(level.upper(), self.LEVELS["DEBUG"])
            
            handler_config = {
                "format": format,
                "level": level_num,
                "colorize": colorize,
                "serialize": serialize,
                "backtrace": backtrace,
                "diagnose": diagnose,
                "enqueue": enqueue,
                "catch": catch,
            }
            
            self._handlers.append((handler_id, sink, handler_config))
            
            return handler_id
    
    def remove(self, handler_id: Optional[int] = None) -> None:
        """
        Remove a handler by ID.
        
        Args:
            handler_id: ID of the handler to remove, or None to remove all
        """
        with self._lock:
            if handler_id is None:
                self._handlers.clear()
            else:
                self._handlers = [
                    (hid, sink, config)
                    for hid, sink, config in self._handlers
                    if hid != handler_id
                ]
    
    def bind(self, **context) -> "Logger":
        """
        Create a new logger with additional context.
        
        Args:
            **context: Context variables to bind
        
        Returns:
            A new Logger instance with bound context
        """
        new_logger = Logger.__new__(Logger)
        new_logger._handlers = self._handlers
        new_logger._context = {**self._context, **context}
        new_logger._lock = self._lock
        new_logger._handler_id_counter = self._handler_id_counter
        new_logger._default_handler_id = getattr(self, "_default_handler_id", None)
        return new_logger
    
    def opt(
        self,
        *,
        exception: bool = False,
        record: bool = False,
        lazy: bool = False,
        capture: bool = True,
        colors: bool = False,
        raw: bool = False,
        **kwargs
    ) -> "Logger":
        """
        Create a new logger with options.
        
        Args:
            exception: Whether to include exception info
            record: Whether to include record info
            lazy: Whether to use lazy evaluation
            capture: Whether to capture variables
            colors: Whether to use colors
            raw: Whether to output raw format
            **kwargs: Additional options
        
        Returns:
            A new Logger instance with options
        """
        new_logger = Logger.__new__(Logger)
        new_logger._handlers = self._handlers
        new_logger._context = self._context.copy()
        new_logger._lock = self._lock
        new_logger._handler_id_counter = self._handler_id_counter
        new_logger._default_handler_id = getattr(self, "_default_handler_id", None)
        new_logger._opt_exception = exception
        new_logger._opt_record = record
        new_logger._opt_lazy = lazy
        new_logger._opt_capture = capture
        new_logger._opt_colors = colors
        new_logger._opt_raw = raw
        return new_logger
    
    def _log(
        self,
        level: str,
        message: str,
        *args,
        **kwargs
    ) -> None:
        """
        Internal logging method.
        
        Args:
            level: Log level name
            message: Log message
            *args: Positional arguments for message formatting
            **kwargs: Keyword arguments for message formatting
        """
        level_num = self.LEVELS.get(level.upper(), self.LEVELS["INFO"])
        
        # Format the message
        if args:
            try:
                formatted_message = message % args
            except (TypeError, ValueError):
                formatted_message = message
        else:
            formatted_message = message
        
        # Get exception info if needed
        exc_info = None
        if getattr(self, "_opt_exception", False) or kwargs.get("exc_info", False):
            exc_info = sys.exc_info()
        
        # Build the record
        now = datetime.now()
        record = {
            "time": now,
            "level": level_num,
            "level_name": level.upper(),
            "message": formatted_message,
            "name": __name__,
            "context": {**self._context},
            "exc_info": exc_info,
        }
        
        # Send to all handlers
        with self._lock:
            for handler_id, sink, config in self._handlers:
                if level_num >= config["level"]:
                    self._emit(sink, record, config)
    
    def _emit(self, sink: Any, record: Dict[str, Any], config: Dict[str, Any]) -> None:
        """
        Emit a log record to a sink.
        
        Args:
            sink: The sink (file, callable, etc.)
            record: The log record
            config: Handler configuration
        """
        try:
            # Format the message
            formatted = self._format_message(record, config["format"])
            
            # Add exception traceback if present
            if record["exc_info"] and record["exc_info"][0] is not None:
                exc_type, exc_value, exc_tb = record["exc_info"]
                tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
                formatted += "\n" + "".join(tb_lines)
            
            # Send to sink
            if callable(sink):
                sink(formatted)
            elif hasattr(sink, "write"):
                sink.write(formatted + "\n")
                if hasattr(sink, "flush"):
                    sink.flush()
            else:
                # Assume it's a file path
                with open(str(sink), "a") as f:
                    f.write(formatted + "\n")
        
        except Exception:
            if config.get("catch", False):
                pass
            else:
                raise
    
    def _format_message(self, record: Dict[str, Any], format_str: str) -> str:
        """
        Format a log message using the format string.
        
        Args:
            record: The log record
            format_str: The format string
        
        Returns:
            The formatted message
        """
        # Build the format context
        context = {
            "time": self._format_time(record["time"]),
            "level": record["level_name"],
            "name": record["name"],
            "message": record["message"],
        }
        
        # Add bound context variables
        context.update(record["context"])
        
        # Replace format placeholders
        result = format_str
        
        # Handle {time:...} format
        import re
        time_pattern = r"\{time:([^}]+)\}"
        for match in re.finditer(time_pattern, result):
            time_format = match.group(1)
            formatted_time = self._format_time(record["time"], time_format)
            result = result.replace(match.group(0), formatted_time)
        
        # Handle {level: <N} format (padding)
        level_pattern = r"\{level:\s*<\s*(\d+)\s*\}"
        for match in re.finditer(level_pattern, result):
            width = int(match.group(1))
            padded_level = record["level_name"].ljust(width)
            result = result.replace(match.group(0), padded_level)
        
        # Handle simple placeholders
        for key, value in context.items():
            result = result.replace("{" + key + "}", str(value))
        
        return result
    
    def _format_time(self, dt: datetime, format_str: str = "YYYY-MM-DD HH:mm:ss.SSS") -> str:
        """
        Format a datetime object.
        
        Args:
            dt: The datetime object
            format_str: The format string (Loguru style)
        
        Returns:
            The formatted time string
        """
        # Convert Loguru format to Python format
        format_map = {
            "YYYY": "%Y",
            "YY": "%y",
            "MM": "%m",
            "DD": "%d",
            "HH": "%H",
            "mm": "%M",
            "ss": "%S",
            "SSS": "%f",
        }
        
        result = format_str
        for loguru_fmt, python_fmt in format_map.items():
            result = result.replace(loguru_fmt, python_fmt)
        
        # Handle milliseconds specially
        if "%f" in result:
            formatted = dt.strftime(result)
            # Convert microseconds to milliseconds
            formatted = formatted.replace(str(dt.microsecond).zfill(6), str(dt.microsecond // 1000).zfill(3))
            return formatted
        
        return dt.strftime(result)
    
    def trace(self, message: str, *args, **kwargs) -> None:
        """Log a trace message."""
        self._log("TRACE", message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log a debug message."""
        self._log("DEBUG", message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs) -> None:
        """Log an info message."""
        self._log("INFO", message, *args, **kwargs)
    
    def success(self, message: str, *args, **kwargs) -> None:
        """Log a success message."""
        self._log("SUCCESS", message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        """Log a warning message."""
        self._log("WARNING", message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """Log an error message."""
        self._log("ERROR", message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs) -> None:
        """Log a critical message."""
        self._log("CRITICAL", message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs) -> None:
        """Log an exception message."""
        kwargs["exc_info"] = True
        self._log("ERROR", message, *args, **kwargs)