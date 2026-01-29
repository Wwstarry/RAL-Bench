import sys
import time
from datetime import datetime
from typing import Any, Callable, Dict, IO, Optional, TextIO, Union

class Logger:
    def __init__(self):
        self._sinks = []
        self._extra = {}
        self._enabled = True
        self._min_level = "DEBUG"
        self._levels = {
            "TRACE": 5,
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50
        }

    def add(
        self,
        sink: Union[Callable[[str], None], IO[str], str],
        *,
        level: str = "DEBUG",
        format: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        filter: Optional[Union[Dict[str, Any], Callable[[Dict[str, Any]], bool]]] = None,
        colorize: bool = False,
        serialize: bool = False,
        backtrace: bool = True,
        diagnose: bool = True,
        enqueue: bool = False,
        catch: bool = True,
    ) -> int:
        sink_id = len(self._sinks)
        self._sinks.append({
            "sink": sink,
            "level": level,
            "format": format,
            "filter": filter,
            "colorize": colorize,
            "serialize": serialize,
            "backtrace": backtrace,
            "diagnose": diagnose,
            "enqueue": enqueue,
            "catch": catch,
        })
        return sink_id

    def remove(self, sink_id: int) -> None:
        if 0 <= sink_id < len(self._sinks):
            self._sinks.pop(sink_id)

    def bind(self, **kwargs: Any) -> "Logger":
        new_logger = Logger()
        new_logger._sinks = self._sinks.copy()
        new_logger._extra = {**self._extra, **kwargs}
        return new_logger

    def opt(self, *, exception: bool = False, record: bool = False, lazy: bool = False, ansi: bool = False) -> "Logger":
        # Simplified opt implementation
        return self

    def _log(self, level: str, message: str, *args: Any, **kwargs: Any) -> None:
        if not self._enabled or self._levels[level] < self._levels[self._min_level]:
            return

        record = {
            "time": datetime.now(),
            "level": level,
            "message": message.format(*args, **kwargs) if args or kwargs else message,
            "extra": self._extra,
            "exception": kwargs.get("exception"),
        }

        for sink in self._sinks:
            if self._levels[level] < self._levels[sink["level"]]:
                continue

            formatted = sink["format"].format(
                time=record["time"],
                level=record["level"],
                message=record["message"],
                name=__name__,
                function="<function>",
                line=0,
                **record["extra"]
            )

            if callable(sink["sink"]):
                sink["sink"](formatted)
            elif isinstance(sink["sink"], (IO, TextIO)):
                sink["sink"].write(formatted + "\n")
                sink["sink"].flush()
            elif isinstance(sink["sink"], str):
                with open(sink["sink"], "a") as f:
                    f.write(formatted + "\n")

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("DEBUG", message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("INFO", message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("WARNING", message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("ERROR", message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        kwargs["exception"] = True
        self._log("ERROR", message, *args, **kwargs)

    def catch(self, exception=Exception, *, level="ERROR", reraise=False):
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exception as e:
                    self._log(level, "An error occurred", exception=e)
                    if reraise:
                        raise
            return wrapper
        return decorator

_logger = Logger()