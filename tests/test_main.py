from fastapi.testclient import TestClient
from app.main import app
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


def test_calculate_shipping_cost():
    """Перевірка всіх гілок розрахунку вартості доставки."""
    # Доставка по Україні
    assert calculate_shipping_cost("UA", 15.0, True, "regular", False) == 2.0

    # Міжнародна доставка: посилка до 5 кг
    assert calculate_shipping_cost("PL", 3.0, False, "regular", False) == 15.0

    # Міжнародна доставка: понад 5 кг, стандартна доставка
    assert calculate_shipping_cost("DE", 10.0, False, "regular", False) == 25.0
    assert calculate_shipping_cost("US", 25.0, False, "regular", False) == 40.0

    # Міжнародна доставка: експрес (regular vs non-regular, свята)
    assert calculate_shipping_cost("FR", 10.0, True, "regular", True) == 70.0
    assert calculate_shipping_cost("FR", 10.0, True, "regular", False) == 50.0
    assert calculate_shipping_cost("FR", 10.0, True, "gold", False) == 37.5


def test_generate_shipping_tokens():
    """Тест генератора токенів доставки."""
    tokens = generate_shipping_tokens(2)
    assert len(tokens) == 2
    assert "token" in tokens[0]
    assert tokens[0]["status"] == "calculated_shipping_rate"


def test_api_endpoints():
    """Тестування API ендпоінтів FastAPI."""
    # Тест кореневого маршруту
    response = client.get("/")
    assert response.status_code == 200

    # Тест створення замовлення
    order_payload = {
        "items": [{"name": "Test Item", "price": 50.0, "quantity": 2}],
        "customer_tier": "gold",
        "shipping_country": "UA",
        "shipping_weight": 2.5,
        "is_express": False,
        "is_holiday": False,
    }
    order_res = client.post("/orders/", json=order_payload)
    assert order_res.status_code == 200
    assert "order_id" in order_res.json()