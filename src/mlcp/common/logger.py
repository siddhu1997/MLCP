from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Final

import structlog

class LogLevel(str, Enum):
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"

_LEVEL_MAP: Final[dict[LogLevel, int]] = {
    LogLevel.TRACE: logging.DEBUG,  # structlog has trace; map to DEBUG for stdlib
    LogLevel.DEBUG: logging.DEBUG,
    LogLevel.INFO: logging.INFO,
    LogLevel.WARN: logging.WARNING,
    LogLevel.ERROR: logging.ERROR,
}

def _env_level() -> LogLevel:
    val = os.getenv("MLCP_LOG_LEVEL", "INFO").upper()
    try:
        return LogLevel(val)
    except ValueError:
        return LogLevel.INFO

def _configure_once(level: LogLevel) -> None:
    if getattr(_configure_once, "_done", False):  # type: ignore[attr-defined]
        return
    logging.basicConfig(
        format="%(message)s",
        level=_LEVEL_MAP[level],
        handlers=[logging.StreamHandler()],  # use base class; avoids generic type issues
    )
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(_LEVEL_MAP[level]),
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
    )
    setattr(_configure_once, "_done", True)  # type: ignore[attr-defined]

def get_logger(name: str | None = None, level: LogLevel | None = None) -> structlog.BoundLogger:
    lvl = level or _env_level()
    _configure_once(lvl)
    logger = structlog.get_logger(name or "mlcp")
    env = os.getenv("MLCP_ENV", "local")  # local | production
    return logger.bind(env=env)
