from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Lab #1" in response.text


def test_calculate_order_success():
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
    # 140 - 15% (21.0) = 119.0
    assert data["final_price"] == 119.0