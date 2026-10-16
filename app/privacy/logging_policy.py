"""
Logging Policy Definition according to GDPR Privacy by Design principles.

Defines:
- Allowed fields (technical diagnostics, safe metadata)
- Partially masked fields (email, phone, ip for diagnostics)
- Fully redacted fields (passwords, tokens, api keys, session secrets)
- Regular expression patterns for free-form text and exception masking
"""
import re
from typing import Set

# 1. Дозволені технічні метадані (не містять PII)
ALLOWED_METADATA_FIELDS: Set[str] = {
    "timestamp",
    "level",
    "correlation_id",
    "logger",
    "event_type",
    "action",
    "status",
    "actor_id",
    "subject_id",
    "latency_ms",
    "method",
    "path",
    "status_code",
    "error_code",
    "operation",
    "component",
}

# 2. Заборонені поля (повністю замінюються на [REDACTED])
REDACTED_FIELD_PATTERNS: Set[str] = {
    "password",
    "passwd",
    "pass",
    "user_password",
    "hashed_password",
    "token",
    "access_token",
    "refresh_token",
    "reset_token",
    "auth_token",
    "secret",
    "session_secret",
    "client_secret",
    "secret_key",
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credit_card",
    "card_number",
    "cvv",
    "cvc",
    "ssn",
    "private_key",
}

# 3. Поля, які частково маскуються (зберігається діагностична цінність)
MASKED_PII_FIELDS: Set[str] = {
    "email",
    "email_address",
    "user_email",
    "phone",
    "phone_number",
    "telephone",
    "mobile",
    "full_name",
    "first_name",
    "last_name",
    "name",
    "ip_address",
    "client_ip",
    "address",
}

# Регулярні вирази для санітизації довільного тексту, exception messages та traceback
REDACTED_PLACEHOLDER = "[REDACTED]"

# Email pattern: user.name@domain.com (excludes already masked emails)
EMAIL_REGEX = re.compile(
    r'(?<!\*)\b([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b'
)

# Phone pattern: +380501234567, (050) 123-45-67, +1-555-123-4567, etc.
PHONE_REGEX = re.compile(
    r'(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b'
)

# Bearer / API token pattern in text
BEARER_REGEX = re.compile(
    r'(?i)\b(bearer\s+)([a-zA-Z0-9._~+/-]{8,})\b'
)

# Key-value secret patterns in text (quoted and unquoted)
SECRET_QUOTED_REGEX = re.compile(
    r'(?i)\b(password|passwd|pass|token|access_token|refresh_token|secret|client_secret|api_?key|session_secret|auth_token)'
    r'(\s*[:=]\s*)(["\'])(.*?)\3'
)

SECRET_UNQUOTED_REGEX = re.compile(
    r'(?i)\b(password|passwd|pass|token|access_token|refresh_token|secret|client_secret|api_?key|session_secret|auth_token)'
    r'(\s*[:=]\s*)([^\s,;{}()\[\]]+)'
)
