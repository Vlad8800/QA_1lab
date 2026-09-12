import secrets
from typing import Any, Dict, List


def calculate_base_total(items: List[Dict[str, Any]]) -> float:
    """Обчислення базової вартості всіх позицій замовлення."""
    return sum(float(item["price"]) * int(item["quantity"]) for item in items)


def apply_loyalty_discount(subtotal: float, tier: str) -> float:
    """Розрахунок вартості з урахуванням знижки за рівнем клієнта."""
    discount_map = {
        "gold": 0.15,
        "vip": 0.15,
        "silver": 0.10,
        "premium": 0.10,
    }
    discount_rate = discount_map.get(tier.lower(), 0.0)
    return round(subtotal * (1.0 - discount_rate), 2)


def calculate_shipping_cost(
    country_code: str,
    weight: float,
    is_express: bool,
    customer_tier: str,
    is_holiday: bool,
) -> float:
    """Розрахунок вартості доставки залежно від країни, ваги та терміновості."""
    if country_code.upper() == "UA":
        return 2.0

    base_rate = 15.0 if weight <= 5.0 else 25.0
    if weight > 20.0:
        base_rate += 15.0

    if is_express:
        multiplier = 2.0 if customer_tier.lower() == "regular" else 1.5
        holiday_surcharge = 20.0 if is_holiday else 0.0
        return (base_rate * multiplier) + holiday_surcharge

    return base_rate


def generate_shipping_tokens(count: int = 3) -> List[Dict[str, str]]:
    """Генерація криптографічно стійких токенів для відстеження посилки."""
    return [
        {
            "token": secrets.token_hex(16),
            "status": "calculated_shipping_rate",
        }
        for _ in range(count)
    ]