"""
Automated Integration Test Suite for Step 2: Personal Data Export & GDPR Right of Access.

Validates:
- Structured, versioned export contract (GET /api/users/{id}/personal-data)
- Data aggregation across profile, settings, history, orders, consents
- Strict Data Minimization: Zero exposure of password hashes, reset tokens, antifraud scores
- Anti-IDOR Access Control: Strict rejection when user A requests user B's data
- Privilege delegation: Lawful export by DPO / Admin
- Documented Omissions for accounts without orders/activity
- Privacy-safe audit trail without dumping exported PII into logs
"""
import io
import json
import logging
import uuid
import pytest
from fastapi.testclient import TestClient

from app.export.repository import UserDataRepository
from app.export.service import PersonalDataExportService
from app.main import app
from app.privacy import setup_privacy_logging

client = TestClient(app)

# Known sensitive fields stored in DB that MUST NEVER be present in the export
PROHIBITED_SECURITY_FIELDS = [
    "password_hash",
    "salt",
    "password_reset_token",
    "security_question",
    "security_answer_hash",
    "antifraud_score",
    "is_flagged_fraud",
    "internal_risk_level",
    "internal_notes",
]

# Sensitive raw values from repo that MUST NEVER leak into the HTTP response body
RAW_SENSITIVE_DB_VALUES = [
    "$2b$12$e8x5Z89Z.fakehashvalue9912093840293482039482034982039",
    "rst_tok_991823901823091283",
    "secret_hashed_answer_12345",
]


@pytest.fixture
def export_log_capture():
    """Fixture that captures logging output during export operations."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = setup_privacy_logging(log_level=logging.INFO, json_format=True, handler=handler)
    yield stream
    for h in list(logger.handlers):
        logger.removeHandler(h)


# ==============================================================================
# 1. ТЕСТ СТРУКТУРИ КОНТРАКТУ ТА АГРЕГАЦІЇ ДАНИХ (Article 15 Right of Access)
# ==============================================================================

def test_successful_personal_data_export_aggregation():
    """
    Позитивний сценарій:
    1. Авторизований користувач успішно експортує власні дані.
    2. Перевіряється агрегація 5 категорій: profile, settings, activity_history, orders, consents.
    3. Перевіряється стабільність метаданих (schema_version=1.0.0, ISO-8601 UTC timestamp).
    """
    custom_cid = f"exp-cid-{uuid.uuid4()}"
    headers = {
        "X-Actor-ID": "usr_101",
        "X-Actor-Role": "user",
        "X-Correlation-ID": custom_cid,
    }

    # Тестуємо як основний шлях /api/users/{id}/personal-data, так і версіонований /api/v1/...
    for endpoint in ["/api/users/usr_101/personal-data", "/api/v1/users/usr_101/personal-data"]:
        response = client.get(endpoint, headers=headers)
        assert response.status_code == 200, f"Failed at {endpoint}"

        data = response.json()

        # 1. Метадані експорту
        assert data["schema_version"] == "1.0.0"
        assert data["subject_id"] == "usr_101"
        assert data["export_id"].startswith("exp_")
        assert "generated_at" in data

        # 2. Категорії
        categories = data["data_categories"]
        assert "profile" in categories
        assert "settings" in categories
        assert "activity_history" in categories
        assert "orders" in categories
        assert "consents" in categories

        # 3. Перевірка коректності агрегованих даних
        profile = data["profile"]
        assert profile["full_name"] == "Олександр Коваленко"
        assert profile["email"] == "oleksandr.kovalenko@example.ua"
        assert profile["phone_number"] == "+380501112233"

        settings = data["settings"]
        assert settings["language"] == "uk"
        assert settings["theme"] == "dark"

        assert len(data["activity_history"]) == 2
        assert data["activity_history"][0]["action"] == "USER_LOGIN"

        assert len(data["orders"]) == 2
        assert data["orders"][0]["order_id"] == "ord_9001"
        assert data["orders"][0]["total_amount"] == 1250.50

        assert len(data["consents"]) == 2
        assert data["consents"][0]["purpose"] == "MARKETING_EMAIL"
        assert data["consents"][0]["is_granted"] is True


# ==============================================================================
# 2. ТЕСТ МІНІМІЗАЦІЇ ДАНИХ (Data Minimization & Exclusion of Security Fields)
# ==============================================================================

def test_data_minimization_strict_exclusion_of_security_fields():
    """
    Сувора перевірка мінімізації даних:
    Переконуємося, що жодне технічне або безпекове поле (password_hash,
    reset_token, security_answers, antifraud_score) не потрапило у відповідь.
    """
    headers = {"X-Actor-ID": "usr_101"}
    response = client.get("/api/users/usr_101/personal-data", headers=headers)
    assert response.status_code == 200

    response_text = response.text
    response_json = response.json()

    # 1. Перевірка за назвами ключів (заборонені поля не повинні існувати ніде у відповіді)
    for forbidden_key in PROHIBITED_SECURITY_FIELDS:
        assert forbidden_key not in response_text, (
            f"SECURITY VIOLATION: Forbidden security field '{forbidden_key}' found in export body!"
        )

    # 2. Перевірка за конкретними сирими значеннями з бази даних
    for raw_secret in RAW_SENSITIVE_DB_VALUES:
        assert raw_secret not in response_text, (
            f"SECURITY VIOLATION: Raw security value '{raw_secret}' leaked in export response!"
        )

    # 3. Перевірка словника профілю
    profile = response_json["profile"]
    assert "password_hash" not in profile
    assert "antifraud_score" not in profile


# ==============================================================================
# 3. ТЕСТ КОНТРОЛЮ ДОСТУПУ ТА ЗАХИСТУ ВІД IDOR (Anti-IDOR Authorization)
# ==============================================================================

def test_idor_protection_foreign_user_access_blocked():
    """
    Anti-IDOR тест:
    Користувач usr_102 намагається отримати експорт даних користувача usr_101.
    Очікується контрольована відмова 403 Forbidden без розкриття чужих даних.
    """
    headers = {
        "X-Actor-ID": "usr_102",  # Сторонній користувач
        "X-Actor-Role": "user",
    }
    response = client.get("/api/users/usr_101/personal-data", headers=headers)

    # Повинен повернути 403 Forbidden
    assert response.status_code == 403
    error_body = response.json()
    assert "Access denied" in error_body["detail"]

    # Перевірка: в тілі відповіді відсутні будь-які персональні дані usr_101
    assert "Олександр Коваленко" not in response.text
    assert "oleksandr.kovalenko" not in response.text


def test_unauthenticated_request_rejected():
    """Спроба експорту без автентифікації відхиляється статусом 401 Unauthorized."""
    response = client.get("/api/users/usr_101/personal-data")
    assert response.status_code == 401
    assert "Authentication credentials" in response.json()["detail"]


def test_bearer_token_authentication_support():
    """Підтримка автентифікації через стандартний заголовок Authorization: Bearer."""
    headers = {"Authorization": "Bearer usr_101"}
    response = client.get("/api/users/usr_101/personal-data", headers=headers)
    assert response.status_code == 200
    assert response.json()["subject_id"] == "usr_101"


def test_dpo_privileged_export_access():
    """
    Правомірний доступ Data Protection Officer (DPO) або Admin:
    Уповноважена особа може експортувати дані суб'єкта на законній підставі.
    """
    headers = {
        "X-Actor-ID": "dpo_officer_42",
        "X-Actor-Role": "dpo",
    }
    response = client.get("/api/users/usr_101/personal-data", headers=headers)
    assert response.status_code == 200
    assert response.json()["subject_id"] == "usr_101"


def test_nonexistent_subject_returns_404():
    """Запит для неіснуючого користувача повертає 404 Not Found."""
    headers = {"X-Actor-ID": "usr_9999"}
    response = client.get("/api/users/usr_9999/personal-data", headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ==============================================================================
# 4. ТЕСТ ДОКУМЕНТОВАНИХ ОПУЩЕНЬ (Documented Omissions for Empty Categories)
# ==============================================================================

def test_documented_omissions_for_empty_sources():
    """
    Перевірка передбачуваної структури для категорій без записів:
    Для usr_103 немає замовлень та історії активності.
    Замість помилки чи тихого зникнення категорій система повертає documented omissions.
    """
    headers = {"X-Actor-ID": "usr_103"}
    response = client.get("/api/users/usr_103/personal-data", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["orders"] == []
    assert data["activity_history"] == []

    omissions = {o["category"]: o["reason"] for o in data["documented_omissions"]}
    assert "orders" in omissions
    assert "activity_history" in omissions
    assert "No commercial orders" in omissions["orders"] or "not created" in omissions["orders"]


# ==============================================================================
# 5. ТЕСТ ВІДСУТНОСТІ ВИТОКУ PII У ЛОГАХ ПІД ЧАС ЕКСПОРТУ
# ==============================================================================

def test_privacy_safe_audit_logging_during_export(export_log_capture):
    """
    Перевірка відсутності витоку PII через лог-файли під час експорту:
    1. Журнал містить подію успішного експорту та технічні метадані.
    2. Журнал НЕ містить повного дампу експортованого JSON чи відкритих PII.
    """
    headers = {
        "X-Actor-ID": "usr_101",
        "X-Correlation-ID": "audit-export-trace-77",
    }
    response = client.get("/api/users/usr_101/personal-data", headers=headers)
    assert response.status_code == 200

    captured_logs = export_log_capture.getvalue()
    assert captured_logs, "Logs should have recorded the export event"

    # Перевірка: факт операції зафіксовано
    assert "PERSONAL_DATA_EXPORT_SUCCESS" in captured_logs
    assert "audit-export-trace-77" in captured_logs

    # СТРОГА ПЕРЕВІРКА: Сирі конфіденційні адреси чи повний dump не повинні бути в логах
    assert "вул. Хрещатик, 24" not in captured_logs
    assert "password_hash" not in captured_logs

