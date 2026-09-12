"""
Order processing service containing business logic for calculations.
"""
from typing import List, Dict, Any


def calculate_base_total(items: List[Dict[str, Any]]) -> float:
    """Calculates subtotal for given order items."""
    total = 0.0
    for item in items:
        price = float(item.get("price", 0.0))
        qty = int(item.get("quantity", 1))
        if price > 0 and qty > 0:
            total += price * qty
    return round(total, 2)


def apply_loyalty_discount(subtotal: float, customer_tier: str) -> float:
    """Applies clean, straightforward customer loyalty discounts."""
    tier_rates = {
        "bronze": 0.05,
        "silver": 0.10,
        "gold": 0.15,
        "vip": 0.20,
    }
    discount_rate = tier_rates.get(customer_tier.lower(), 0.0)
    discount_amount = subtotal * discount_rate
    return round(subtotal - discount_amount, 2)