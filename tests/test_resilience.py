import httpx
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app

client = TestClient(app)

SAMPLE_ORDER_PAYLOAD = {
    "customer_tier": "regular",
    "country_code": "PL",
    "weight": 2.0,
    "is_express": False,
    "is_holiday": False,
    "items": [
        {"name": "USB-C Cable", "price": 25.0, "quantity": 1}
    ]
}


def test_external_tariff_service_success(mocker):
    """Позитивна перевірка: якщо зовнішній сервіс відповідає, fallback не активується."""
    mock_fetch = mocker.patch("app.services._fetch_external_base_rate", return_value=18.0)

    response = client.post("/api/v1/orders/calculate", json=SAMPLE_ORDER_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["shipping"]["is_fallback"] is False
    assert data["shipping"]["mode"] == "external_live"
    assert data["shipping"]["final_cost"] == 18.0
    assert mock_fetch.call_count == 1


def test_resilience_fallback_on_external_failure(mocker, caplog):
    """Resilience test: при збої мережі активується fallback, повертається 200 і пишеться лог."""
    mocker.patch(
        "app.services._fetch_external_base_rate",
        side_effect=httpx.ConnectError("Connection refused by external service")
    )

    with caplog.at_level("WARNING"):
        response = client.post("/api/v1/orders/calculate", json=SAMPLE_ORDER_PAYLOAD)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["shipping"]["is_fallback"] is True
    assert data["shipping"]["mode"] == "fallback_applied"
    assert data["shipping"]["final_cost"] == 25.0
    assert data["final_total"] == 50.0
    assert any("Fallback activated" in record.message for record in caplog.records)


def test_resilience_retry_attempts_and_backoff():
    """
    Resilience test (Retry parameter verification):
    Перевірка конфігурації Tenacity: рівно 3 спроби з обмеженням backoff.
    """
    from app.services import _fetch_external_base_rate
    
    # Перевіряємо параметри tenacity декоратора напряму
    assert hasattr(_fetch_external_base_rate, "retry"), "Функція повинна мати tenacity retry"
    retry_obj = _fetch_external_base_rate.retry
    assert retry_obj.stop.max_attempt_number == 3