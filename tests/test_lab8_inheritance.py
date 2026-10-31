"""Vertical architecture experiment on a real shipping quote endpoint."""

from fastapi.testclient import TestClient

from app.main import app
from app.services import ShippingOrderSpec
from app.shipping_policy import ExpressHolidayShippingQuote, RegionalShippingQuote


def pl_spec(tier="regular"):
    return ShippingOrderSpec(
        country_code="PL", weight=6.0, is_express=True,
        customer_tier=tier, is_holiday=True,
    )


def test_regional_rule_calls_base_quote_for_foreign_country():
    assert RegionalShippingQuote().quote(pl_spec(), 25.0) == 80.0


def test_deep_rule_applies_vip_incentive_after_parent_quote():
    policy = ExpressHolidayShippingQuote()
    assert policy.quote(pl_spec("vip"), 25.0) == 61.75
    assert policy.mode(pl_spec("vip"), True) == "express_holiday:fallback_applied"


def test_shipping_policy_http_path_uses_deep_rule():
    response = TestClient(app).post("/api/v1/orders/quote-with-policy", json={
        "country_code": "PL", "weight": 6.0, "base_rate": 25.0,
        "is_express": True, "customer_tier": "vip", "is_holiday": True,
        "is_fallback": True,
    })
    assert response.status_code == 200
    assert response.json()["final_cost"] == 61.75
    assert response.json()["mode"] == "express_holiday:fallback_applied"


def test_domestic_policy_keeps_local_rate():
    spec = ShippingOrderSpec(country_code="UA", weight=6.0)
    assert RegionalShippingQuote().quote(spec, 2.0) == 2.0
