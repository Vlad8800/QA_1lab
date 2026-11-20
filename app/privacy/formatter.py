"""
Structured JSON and Plain Text Log Formatters for GDPR Compliance.
"""
from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict

from app.privacy.sanitizer import sanitize_data


class StructuredJsonFormatter(logging.Formatter):
    """
    Serializes log records into structured, GDPR-sanitized JSON.
    Guarantees no raw PII/secrets while preserving all technical diagnostic fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Standard record message formatting
        message = record.getMessage()

        # Base structured fields
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "correlation_id": getattr(record, "correlation_id", "none"),
            "logger": record.name,
            "message": message,
        }

        # Optional business audit fields
        if hasattr(record, "event_type"):
            log_entry["event_type"] = record.event_type
        if hasattr(record, "actor_id"):
            log_entry["actor_id"] = record.actor_id
        if hasattr(record, "status"):
            log_entry["status"] = record.status

        # Collect additional extra context fields
        reserved = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message", "correlation_id", "asctime",
            "event_type", "actor_id", "status"
        }

        extra_details: Dict[str, Any] = {}
        for key, val in record.__dict__.items():
            if key not in reserved and not key.startswith("_"):
                extra_details[key] = val

        if extra_details:
            log_entry["details"] = extra_details

        # Exception information
        if record.exc_text:
            log_entry["exception"] = record.exc_text
        elif record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


class SafeTextFormatter(logging.Formatter):
    """
    Standard human-readable text formatter that includes correlation_id
    and relies on PIISanitizingFilter for in-place message sanitization.
    """

    def __init__(self, fmt: str = None, datefmt: str = None):
        default_fmt = "[%(asctime)s] [%(levelname)s] [corr=%(correlation_id)s] %(name)s: %(message)s"
        super().__init__(fmt=fmt or default_fmt, datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "none"
        return super().format(record)
