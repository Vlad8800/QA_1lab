"""
Logging filter for automatic centralized sanitization and correlation ID propagation.
"""
import logging
from typing import Any

from app.privacy.context import get_correlation_id
from app.privacy.logging_policy import REDACTED_PLACEHOLDER
from app.privacy.sanitizer import (
    _is_masked_key,
    _is_redacted_key,
    mask_email,
    mask_ip,
    mask_name,
    mask_phone,
    sanitize_data,
    sanitize_record,
)


class PIISanitizingFilter(logging.Filter):
    """
    Centralized logging filter that ensures every log entry:
    1. Contains correlation_id if set in async context
    2. Strips and redacts any PII and sensitive credentials in-place
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # Attach correlation_id from context if not present
        if not getattr(record, "correlation_id", None):
            cid = get_correlation_id()
            record.correlation_id = cid if cid else "none"

        # Sanitize standard log record fields
        sanitize_record(record)

        # Sanitize any custom extra attributes passed to the logger
        standard_attrs = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message", "correlation_id", "asctime"
        }

        for attr, value in list(record.__dict__.items()):
            if attr not in standard_attrs and not attr.startswith("_"):
                str_attr = str(attr)
                if _is_redacted_key(str_attr):
                    record.__dict__[attr] = REDACTED_PLACEHOLDER
                elif _is_masked_key(str_attr) and isinstance(value, str):
                    attr_lower = str_attr.lower()
                    if "email" in attr_lower:
                        record.__dict__[attr] = mask_email(value)
                    elif "phone" in attr_lower or "mobile" in attr_lower or "tel" in attr_lower:
                        record.__dict__[attr] = mask_phone(value)
                    elif "ip" in attr_lower:
                        record.__dict__[attr] = mask_ip(value)
                    else:
                        record.__dict__[attr] = mask_name(value)
                else:
                    record.__dict__[attr] = sanitize_data(value)

        return True
