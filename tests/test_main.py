from fastapi.testclient import TestClient
from app.main import app
from app.services import (
    calculate_base_total,
    apply_loyalty_discount,
    calculate_shipping_cost,
    generate_shipping_tokens,
)

client = TestClient(app)


def test_calculate_order_success():
    """Тест ендпоінта розрахунку замовлення."""
    payload = {
        "customer_tier": "gold",
        "items": [
            {"name": "Keyboard", "price": 100.0, "quantity": 1},
            {"name": "Keycaps", "price": 20.0, "quantity": 2},
        ],
    }
    response = client.post("/api/v1/orders/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["subtotal"] == 140.0
    assert data["final_price"] == 119.0


def test_calculate_base_total():
    """Перевірка обчислення суми порожнього та наповненого кошика."""
    assert calculate_base_total([]) == 0.0
    items = [{"price": 10.5, "quantity": 2}, {"price": 5.0, "quantity": 1}]
    assert calculate_base_total(items) == 26.0


def test_apply_loyalty_discount():
    """Перевірка всіх рівнів програми лояльності."""
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
    assert calculate_shipping_cost("FR", 10.0, True, "regular", False) == 90.0
    assert calculate_shipping_cost("FR", 10.0, True, "vip", False) == 60.0


def test_generate_shipping_tokens():
    """Перевірка генерації криптографічних токенів."""
    tokens = generate_shipping_tokens(count=5)
    assert len(tokens) == 5
    assert "token" in tokens[0]
    assert tokens[0]["status"] == "calculated_shipping_rate"
    assert len(tokens[0]["token"]) == 32  # hex-рядок 16 байт