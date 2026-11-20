"""
Automated Test Suite for Step 1: Secure Logging & PII Masking (Lab #4).

Validates:
- Centralized sanitization of plain-text messages
- Structured JSON logging with diagnostic metadata (timestamp, correlation_id)
- Exception messages and stacktrace sanitization
- Absence of raw request/response body logging in FastAPI middleware
- Negative test scenario: Detection and redaction of nested DTOs and exception payloads
- Zero-leakage verification: Test fails if any raw sensitive value appears in logs
"""
import io
import json
import logging
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.privacy import (
    ALLOWED_METADATA_FIELDS,
    MASKED_PII_FIELDS,
    PIISanitizingFilter,
    PrivacyLoggingMiddleware,
    REDACTED_FIELD_PATTERNS,
    REDACTED_PLACEHOLDER,
    StructuredJsonFormatter,
    get_correlation_id,
    mask_email,
    mask_phone,
    sanitize_data,
    sanitize_text,
    set_correlation_id,
    setup_privacy_logging,
)

# Known synthetic test credentials & PII (synthetic only, no real user data)
SYNTHETIC_EMAIL = "developer.test@corporation.ua"
SYNTHETIC_PHONE = "+380509876543"
SYNTHETIC_PASSWORD = "VerySecretPassword!2026"
SYNTHETIC_BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy_payload"
SYNTHETIC_API_KEY = "YOUR_SYNTHETIC_KEY"  # gitleaks:allow
SYNTHETIC_SESSION_SECRET = "sess_secret_random_hex_99999"

RAW_SENSITIVE_VALUES = [
    SYNTHETIC_EMAIL,
    SYNTHETIC_PHONE,
    SYNTHETIC_PASSWORD,
    SYNTHETIC_BEARER_TOKEN,
    SYNTHETIC_API_KEY,
    SYNTHETIC_SESSION_SECRET,
]


@pytest.fixture
def log_capture():
    """Fixture that configures an in-memory stream log capture with JSON formatting."""
    from app.privacy.context import clear_correlation_id
    clear_correlation_id()
    logging.getLogger("httpx").setLevel(logging.WARNING)
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = setup_privacy_logging(log_level=logging.INFO, json_format=True, handler=handler)
    yield stream
    clear_correlation_id()
    # Reset handlers
    for h in list(logger.handlers):
        logger.removeHandler(h)


def assert_no_raw_sensitive_leaks(captured_output: str, raw_values: list = None):
    """
    Assertion helper: fails immediately if any raw sensitive value
    is present in the captured log stream.
    """
    if raw_values is None:
        raw_values = RAW_SENSITIVE_VALUES

    for sensitive_item in raw_values:
        assert sensitive_item not in captured_output, (
            f"SECURITY LEAK DETECTED: Raw sensitive value '{sensitive_item}' "
            f"found in logs: {captured_output}"
        )


# ==============================================================================
# 1. ТЕСТИ ПОЛІТИКИ ЛОГУВАННЯ
# ==============================================================================

def test_logging_policy_definitions():
    """Перевірка повноти списків дозволених, маскованих і заборонених полів."""
    # Заборонені (повинні містити всі типи автентифікаційних секретів)
    assert "password" in REDACTED_FIELD_PATTERNS
    assert "token" in REDACTED_FIELD_PATTERNS
    assert "api_key" in REDACTED_FIELD_PATTERNS
    assert "session_secret" in REDACTED_FIELD_PATTERNS

    # Масковані (контактні дані, які потребують часткової збереженості)
    assert "email" in MASKED_PII_FIELDS
    assert "phone" in MASKED_PII_FIELDS

    # Дозволені технічні метадані
    assert "correlation_id" in ALLOWED_METADATA_FIELDS
    assert "timestamp" in ALLOWED_METADATA_FIELDS
    assert "level" in ALLOWED_METADATA_FIELDS


def test_helper_masking_functions():
    """Перевірка функцій часткового маскування email та телефону."""
    # Email: повинен зберігати домен та першу/останню літеру імені
    masked_email = mask_email(SYNTHETIC_EMAIL)
    assert masked_email == "d***t@corporation.ua"
    assert SYNTHETIC_EMAIL != masked_email

    # Коротка адреса
    assert mask_email("ab@test.com") == "a***@test.com"

    # Телефон: зберігає префікс країни та останні 4 цифри
    masked_phone = mask_phone(SYNTHETIC_PHONE)
    assert masked_phone.startswith("+380")
    assert masked_phone.endswith("6543")
    assert "****" in masked_phone
    assert SYNTHETIC_PHONE != masked_phone


# ==============================================================================
# 2. ТЕСТИ ЦЕНТРАЛІЗОВАНОГО САНІТИЗАТОРА ДЛЯ РІЗНИХ ФОРМАТІВ
# ==============================================================================

def test_sanitize_plain_text():
    """Тестування маскування PII та секретів у неструктурованому тексті."""
    raw_message = (
        f"User login attempt for {SYNTHETIC_EMAIL} with phone={SYNTHETIC_PHONE}, "
        f"password={SYNTHETIC_PASSWORD}, and auth token Bearer {SYNTHETIC_BEARER_TOKEN}"
    )

    sanitized = sanitize_text(raw_message)

    # 1. Жодного відкритого секрету не повинно залишитися
    assert SYNTHETIC_EMAIL not in sanitized
    assert SYNTHETIC_PHONE not in sanitized
    assert SYNTHETIC_PASSWORD not in sanitized
    assert SYNTHETIC_BEARER_TOKEN not in sanitized

    # 2. Наявні безпечні замінники
    assert "d***t@corporation.ua" in sanitized
    assert "+380****6543" in sanitized
    assert f"password={REDACTED_PLACEHOLDER}" in sanitized
    assert "Bearer [REDACTED]" in sanitized


def test_structured_json_logging(log_capture):
    """
    Тестування структурованого JSON-логу: валідність JSON, наявність
    метаданих (timestamp, correlation_id), рекурсивне маскування полів.
    """
    logger = logging.getLogger("app.orders")
    test_cid = f"test-corr-{uuid.uuid4()}"
    set_correlation_id(test_cid)

    # Логування структурованого об'єкта
    logger.info(
        "Order customer notification dispatched",
        extra={
            "event_type": "CUSTOMER_NOTIFIED",
            "email": SYNTHETIC_EMAIL,
            "phone": SYNTHETIC_PHONE,
            "api_key": SYNTHETIC_API_KEY,
            "customer_tier": "gold",
        }
    )

    output = log_capture.getvalue().strip()
    assert output, "Log output should not be empty"

    # 1. Перевірка відсутності витоку
    assert_no_raw_sensitive_leaks(output, [SYNTHETIC_EMAIL, SYNTHETIC_PHONE, SYNTHETIC_API_KEY])

    # 2. Перевірка валідності JSON-структури
    parsed_json = json.loads(output)
    assert parsed_json["level"] == "INFO"
    assert parsed_json["correlation_id"] == test_cid
    assert "timestamp" in parsed_json
    assert parsed_json["event_type"] == "CUSTOMER_NOTIFIED"

    # 3. Перевірка вмісту вкладених деталей
    details = parsed_json.get("details", {})
    assert details["email"] == "d***t@corporation.ua"
    assert "****" in details["phone"]
    assert details["api_key"] == REDACTED_PLACEHOLDER
    assert details["customer_tier"] == "gold"


def test_exception_message_and_traceback_sanitization(log_capture):
    """
    Тестування перехоплення та маскування PII всередині exception message та stacktrace.
    """
    logger = logging.getLogger("app.security")
    test_cid = "exc-test-corr-id"
    set_correlation_id(test_cid)

    try:
        # Виклик помилки із чутливими аргументами
        raise ValueError(
            f"Authentication failed for user {SYNTHETIC_EMAIL} with secret password={SYNTHETIC_PASSWORD}"
        )
    except Exception:
        logger.exception("Security exception caught during authentication flow")

    output = log_capture.getvalue()
    assert output, "Log output should contain exception"

    # 1. Перевірка відсутності відкритих даних
    assert_no_raw_sensitive_leaks(output, [SYNTHETIC_EMAIL, SYNTHETIC_PASSWORD])

    # 2. Перевірка структури JSON та наявності sanitized exception
    parsed = json.loads(output.strip().split("\n")[-1])
    assert parsed["level"] == "ERROR"
    assert "exception" in parsed
    assert "d***t@corporation.ua" in parsed["exception"]
    assert f"password={REDACTED_PLACEHOLDER}" in parsed["exception"]


# ==============================================================================
# 3. НЕГАТИВНИЙ СЦЕНАРІЙ: ВКЛАДЕНИЙ DTO ТА СТРОГА ВАЛІДАЦІЯ
# ==============================================================================

def test_negative_scenario_deep_nested_dto_and_leak_detection(log_capture):
    """
    Негативний сценарій:
    1. Передача глибоко вкладеного DTO, що містить повний набір чутливих полів
    2. Перевірка, що централізований рекурсивний санітайзер обробляє кожен рівень вкладеності
    3. Автоматичний assert: якщо хоча б одне оригінальне значення залишилося відкритим - FAIL!
    """
    logger = logging.getLogger("app.deep")
    set_correlation_id("deep-nested-cid")

    # Глибоко вкладена структура даних (nested DTO)
    nested_user_dto = {
        "operation": "SYNC_PROFILE",
        "actor": {
            "id": 42,
            "profile": {
                "user_email": SYNTHETIC_EMAIL,
                "phone_number": SYNTHETIC_PHONE,
                "credentials": {
                    "password": SYNTHETIC_PASSWORD,
                    "session_secret": SYNTHETIC_SESSION_SECRET,
                    "tokens": [
                        SYNTHETIC_BEARER_TOKEN,
                        {"api_key": SYNTHETIC_API_KEY}
                    ]
                }
            }
        }
    }

    logger.info("Synchronizing customer profile", extra={"dto": nested_user_dto})

    output = log_capture.getvalue()

    # СТРОГА ПЕРЕВІРКА НА ВИТІК (Тест падає, якщо хоча б одне значення потрапило у відкритому вигляді)
    assert_no_raw_sensitive_leaks(output)

    # Перевірка правильності заміни
    parsed = json.loads(output.strip())
    dto = parsed["details"]["dto"]
    actor_profile = dto["actor"]["profile"]

    assert actor_profile["user_email"] == "d***t@corporation.ua"
    assert "****" in actor_profile["phone_number"]
    assert actor_profile["credentials"]["password"] == REDACTED_PLACEHOLDER
    assert actor_profile["credentials"]["session_secret"] == REDACTED_PLACEHOLDER
    assert actor_profile["credentials"]["tokens"] == REDACTED_PLACEHOLDER


# ==============================================================================
# 4. ТЕСТ FASTAPI MIDDLEWARE ТА ВІДСУТНОСТІ ЗАЙВОГО ЛОГУВАННЯ (NO RAW BODY)
# ==============================================================================

def test_fastapi_middleware_correlation_id_and_no_raw_body_leak(log_capture):
    """
    Тест інтеграції з FastAPI:
    1. Перевірка прокидання Correlation ID через заголовок X-Correlation-ID
    2. Перевірка, що повне тіло запиту/відповіді (raw body) НЕ потрапляє до журналу
    3. Фіксація лише необхідних безпечних діагностичних метаданих (status, method, path, duration)
    """
    client = TestClient(app)
    custom_cid = f"client-req-{uuid.uuid4()}"

    order_payload = {
        "customer_tier": "gold",
        "country_code": "UA",
        "weight": 2.0,
        "is_express": False,
        "is_holiday": False,
        "items": [
            {"name": "Secure Item", "price": 100.0, "quantity": 1}
        ]
    }

    response = client.post(
        "/api/v1/orders/calculate",
        json=order_payload,
        headers={"X-Correlation-ID": custom_cid}
    )

    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == custom_cid

    captured_logs = log_capture.getvalue()
    log_lines = [json.loads(line) for line in captured_logs.strip().split("\n") if line.strip()]

    # Перевірка наявності correlation_id у всіх рядках логу запиту застосунку
    app_lines = [line for line in log_lines if line.get("logger", "").startswith("app")]
    assert len(app_lines) >= 2, "Expected app request start and finish logs"
    for line in app_lines:
        assert line["correlation_id"] == custom_cid

    # Перевірка, що події HTTP зафіксовані
    event_types = [line.get("event_type") for line in log_lines]
    assert "HTTP_REQUEST_START" in event_types
    assert "HTTP_REQUEST_FINISH" in event_types

    # Перевірка: повний сирий payload НЕ записується як окремий dump
    for line in log_lines:
        assert "Secure Item" not in line.get("message", "")
        if "details" in line:
            assert "raw_body" not in line["details"]
            assert "items" not in line["details"]
