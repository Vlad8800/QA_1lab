"""
Privacy Engineering & GDPR Compliance Module.
"""
from app.privacy.context import get_correlation_id, set_correlation_id
from app.privacy.filter import PIISanitizingFilter
from app.privacy.formatter import SafeTextFormatter, StructuredJsonFormatter
from app.privacy.logger import setup_privacy_logging
from app.privacy.logging_policy import (
    ALLOWED_METADATA_FIELDS,
    MASKED_PII_FIELDS,
    REDACTED_FIELD_PATTERNS,
    REDACTED_PLACEHOLDER,
)
from app.privacy.middleware import PrivacyLoggingMiddleware
from app.privacy.sanitizer import (
    mask_email,
    mask_ip,
    mask_name,
    mask_phone,
    sanitize_data,
    sanitize_record,
    sanitize_text,
)

__all__ = [
    "setup_privacy_logging",
    "PrivacyLoggingMiddleware",
    "PIISanitizingFilter",
    "StructuredJsonFormatter",
    "SafeTextFormatter",
    "get_correlation_id",
    "set_correlation_id",
    "mask_email",
    "mask_phone",
    "mask_name",
    "mask_ip",
    "sanitize_text",
    "sanitize_data",
    "sanitize_record",
    "ALLOWED_METADATA_FIELDS",
    "MASKED_PII_FIELDS",
    "REDACTED_FIELD_PATTERNS",
    "REDACTED_PLACEHOLDER",
]

