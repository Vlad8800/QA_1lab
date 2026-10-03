from fastapi.testclient import TestClient
from app.main import app
import app.services as services
from app.services import (
    calculate_base_total,
    apply_loyalty_discount,
    calculate_shipping_cost,
    generate_shipping_tokens,
)

client = TestClient(app)


def test_calculate_base_total():
    """Тест підрахунку базової вартості."""
    items = [
        {"name": "Item 1", "price": 10.0, "quantity": 2},
        {"name": "Item 2", "price": 5.0, "quantity": 1},
    ]
    assert calculate_base_total(items) == 25.0


def test_apply_loyalty_discount():
    """Тест застосування знижок за програмою лояльності."""
    assert apply_loyalty_discount(100.0, "gold") == 85.0
    assert apply_loyalty_discount(100.0, "vip") == 85.0
    assert apply_loyalty_discount(100.0, "silver") == 90.0
    assert apply_loyalty_discount(100.0, "premium") == 90.0
    assert apply_loyalty_discount(100.0, "bronze") == 100.0


def test_calculate_shipping_cost(monkeypatch):
    """Перевірка всіх гілок розрахунку вартості доставки з моком зовнішнього сервісу."""
    # Мокаємо зовнішній тарифний сервіс, щоб він не падав по таймауту в юніт-тестах
    def mock_fetch_rate(country_code: str) -> float:
        if country_code.upper() == "PL":
            return 15.0
        return 20.0

    monkeypatch.setattr(services, "_fetch_external_base_rate", mock_fetch_rate)

    assert (
        calculate_shipping_cost("UA", 15.0, True, "regular", False)["final_cost"]
        == 2.0
    )
    assert (
        calculate_shipping_cost("PL", 3.0, False, "regular", False)["final_cost"]
        == 15.0
    )
    assert (
        calculate_shipping_cost("DE", 10.0, False, "regular", False)["final_cost"]
        == 25.0
    )
    assert (
        calculate_shipping_cost("US", 25.0, False, "regular", False)["final_cost"]
        == 40.0
    )
    assert (
        calculate_shipping_cost("FR", 10.0, True, "regular", True)["final_cost"]
        == 70.0
    )
    assert (
        calculate_shipping_cost("FR", 10.0, True, "regular", False)["final_cost"]
        == 50.0
    )
    assert (
        calculate_shipping_cost("FR", 10.0, True, "gold", False)["final_cost"]
        == 37.5
    )


def test_generate_shipping_tokens():
    """Тест генератора токенів доставки."""
    tokens = generate_shipping_tokens(2)
    assert len(tokens) == 2
    assert "token" in tokens[0]
    assert tokens[0]["status"] == "calculated_shipping_rate"


def test_api_endpoints():
    """Тестування доступних стандартних ендпоінтів FastAPI."""
    # Перевірка головного маршруту
    response = client.get("/")
    assert response.status_code == 200

    # Перевірка документації OpenAPI
    docs_response = client.get("/docs")
    assert docs_response.status_code == 200

    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200