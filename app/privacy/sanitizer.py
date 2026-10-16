"""
Centralized PII and Secrets Sanitization Engine.

Provides deep sanitization for:
- Free-form log text
- Structured objects, dictionaries, lists, and DTOs
- Exception messages and tracebacks
- Logging LogRecord attributes
"""
import copy
import logging
import re
import traceback
from typing import Any, Dict, List, Mapping, Union

from app.privacy.logging_policy import (
    BEARER_REGEX,
    EMAIL_REGEX,
    MASKED_PII_FIELDS,
    PHONE_REGEX,
    REDACTED_FIELD_PATTERNS,
    REDACTED_PLACEHOLDER,
    SECRET_QUOTED_REGEX,
    SECRET_UNQUOTED_REGEX,
)


def mask_email(email: str) -> str:
    """Mask email preserving domain and first/last char of user for diagnostic tracing."""
    if not email or "@" not in email:
        return email
    if "***" in email:
        return email
    parts = email.split("@", 1)
    user, domain = parts[0], parts[1]
    if len(user) <= 2:
        masked_user = f"{user[0]}***"
    else:
        masked_user = f"{user[0]}***{user[-1]}"
    return f"{masked_user}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone preserving country prefix and last 3-4 digits."""
    if "****" in phone or "***" in phone:
        return phone
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    if len(cleaned) <= 6:
        return "***"
    prefix = cleaned[:4]
    suffix = cleaned[-4:]
    return f"{prefix}****{suffix}"


def mask_name(name: str) -> str:
    """Partially mask human names: Ivan Petrenko -> I***n P***o."""
    words = name.strip().split()
    if not words:
        return name
    masked_words = []
    for w in words:
        if len(w) <= 2:
            masked_words.append(f"{w[0]}*")
        else:
            masked_words.append(f"{w[0]}***{w[-1]}")
    return " ".join(masked_words)


def mask_ip(ip: str) -> str:
    """Mask IP preserving network subnet: 192.168.1.42 -> 192.168.1.***."""
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.***"
    return "***"


def sanitize_text(text: str) -> str:
    """
    Sanitize sensitive patterns inside unstructured text strings.
    Handles secrets, bearer tokens, emails, and phone numbers.
    """
    if not isinstance(text, str) or not text:
        return text

    # 1. Key-value secrets replacement (quoted and unquoted)
    result = SECRET_QUOTED_REGEX.sub(
        lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}{REDACTED_PLACEHOLDER}{m.group(3)}",
        text
    )
    result = SECRET_UNQUOTED_REGEX.sub(
        lambda m: f"{m.group(1)}{m.group(2)}{REDACTED_PLACEHOLDER}",
        result
    )

    # 2. Bearer authorization header tokens
    result = BEARER_REGEX.sub(r"\1[REDACTED]", result)

    # 3. Email masking
    result = EMAIL_REGEX.sub(lambda m: mask_email(m.group(0)), result)

    # 4. Phone masking (only if length >= 9 to prevent masking short IDs/numbers)
    def _replace_phone(m: re.Match) -> str:
        val = m.group(0)
        digits = re.sub(r'\D', '', val)
        if len(digits) >= 9:
            return mask_phone(val)
        return val

    result = PHONE_REGEX.sub(_replace_phone, result)

    return result


def _is_redacted_key(key: str) -> bool:
    """Check if dictionary key represents a confidential credential/secret."""
    k_lower = key.lower()
    return any(pattern in k_lower for pattern in REDACTED_FIELD_PATTERNS)


def _is_masked_key(key: str) -> bool:
    """Check if dictionary key represents PII requiring partial masking."""
    k_lower = key.lower()
    return any(pattern in k_lower for pattern in MASKED_PII_FIELDS)


def _sanitize_masked_value(key: str, val: Any, seen: set) -> Any:
    """Helper to mask individual value based on key category."""
    if not isinstance(val, str):
        return sanitize_data(val, seen)
    k_lower = key.lower()
    if "email" in k_lower:
        return mask_email(val)
    if any(p in k_lower for p in ("phone", "mobile", "tel")):
        return mask_phone(val)
    if "ip" in k_lower:
        return mask_ip(val)
    return mask_name(val)


def _sanitize_mapping(data: Mapping, seen: set) -> Dict[str, Any]:
    """Helper to sanitize dict-like mappings."""
    sanitized_dict: Dict[str, Any] = {}
    for k, v in data.items():
        str_key = str(k)
        if _is_redacted_key(str_key):
            sanitized_dict[str_key] = REDACTED_PLACEHOLDER
        elif _is_masked_key(str_key):
            sanitized_dict[str_key] = _sanitize_masked_value(str_key, v, seen)
        else:
            sanitized_dict[str_key] = sanitize_data(v, seen)
    return sanitized_dict


def _sanitize_tuple(data: tuple, seen: set) -> tuple:
    """Helper to sanitize tuples and namedtuples safely."""
    sanitized_items = [sanitize_data(item, seen) for item in data]
    if hasattr(data, "_fields"):
        try:
            return type(data)(*sanitized_items)
        except Exception:
            return tuple(sanitized_items)
    return tuple(sanitized_items)


def sanitize_data(data: Any, seen: set = None) -> Any:
    """
    Recursively sanitize structured data (dicts, lists, DTOs, exceptions).
    Protects against infinite recursion in circular references.
    """
    if seen is None:
        seen = set()

    if data is None:
        return None

    # Handle Pydantic models or objects with model_dump/dict
    if hasattr(data, "model_dump") and callable(data.model_dump):
        data = data.model_dump()
    elif hasattr(data, "dict") and callable(data.dict):
        data = data.dict()
    elif hasattr(data, "__dict__") and not isinstance(data, (type, logging.LogRecord, BaseException)):
        data = copy.copy(data.__dict__)

    data_id = id(data)
    if data_id in seen:
        return "[CIRCULAR_REFERENCE]"

    if isinstance(data, Mapping):
        seen.add(data_id)
        result = _sanitize_mapping(data, seen)
        seen.remove(data_id)
        return result

    if isinstance(data, list):
        seen.add(data_id)
        result = [sanitize_data(item, seen) for item in data]
        seen.remove(data_id)
        return result

    if isinstance(data, set):
        seen.add(data_id)
        result = {sanitize_data(item, seen) for item in data}
        seen.remove(data_id)
        return result

    if isinstance(data, tuple):
        seen.add(data_id)
        result = _sanitize_tuple(data, seen)
        seen.remove(data_id)
        return result

    if isinstance(data, str):
        return sanitize_text(data)

    if isinstance(data, BaseException):
        exc_msg = sanitize_text(str(data))
        return f"{type(data).__name__}: {exc_msg}"

    return data


def sanitize_record(record: logging.LogRecord) -> None:
    """
    In-place sanitization of a logging.LogRecord instance.
    Sanitizes message, arguments, extra fields, and exception info.
    """
    # 1. Sanitize main message template
    if isinstance(record.msg, str):
        record.msg = sanitize_text(record.msg)
    elif isinstance(record.msg, (dict, list, tuple)):
        record.msg = sanitize_data(record.msg)

    # 2. Sanitize positional arguments (record.args)
    if record.args:
        if isinstance(record.args, tuple):
            record.args = tuple(sanitize_data(arg) for arg in record.args)
        elif isinstance(record.args, dict):
            record.args = sanitize_data(record.args)
        else:
            record.args = sanitize_data(record.args)

    # 3. Sanitize exception message and formatted traceback
    if record.exc_text:
        record.exc_text = sanitize_text(record.exc_text)

    if record.exc_info:
        exc_type, exc_val, exc_tb = record.exc_info
        if exc_val is not None:
            # Format and sanitize full traceback string
            raw_tb = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
            record.exc_text = sanitize_text(raw_tb)
