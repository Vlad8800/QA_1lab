import secrets

# ==========================================
# БАЗОВІ ФУНКЦІЇ ПРОЄКТУ (НЕОБХІДНІ ДЛЯ ТЕСТІВ)
# ==========================================

def calculate_base_total(items: list) -> float:
    """Обчислює базову суму замовлення."""
    return sum(item["price"] * item["quantity"] for item in items)


def apply_loyalty_discount(total: float, customer_type: str) -> float:
    """Застосовує знижку програми лояльності."""
    if customer_type == "vip":
        return total * 0.85
    elif customer_type == "premium":
        return total * 0.90
    return total


# ==========================================
# РЕФАКТОРИНГ (ЗАВДАННЯ 4: СТАН PASS)
# ==========================================

def _get_international_shipping_surcharge(weight: float, express: bool, is_holiday: bool, is_regular: bool) -> float:
    """Ізольований розрахунок надбавки (Extract Method)."""
    if not express:
        return 30.0 if weight > 20 else 15.0

    if is_regular:
        return 100.0 if is_holiday else 80.0
    return 50.0


def calculate_shipping_cost(country: str, weight: float, express: bool, customer_type: str, is_holiday: bool) -> float:
    """
    Оптимізована функція із застосуванням Guard Clauses.
    Cognitive Complexity = 3 (замість 18).
    """
    if country == "UA":
        return 2.0

    base_cost = 10.0
    if weight <= 5:
        return base_cost + 5.0

    is_regular = (customer_type == "regular")
    surcharge = _get_international_shipping_surcharge(weight, express, is_holiday, is_regular)
    return base_cost + surcharge


def generate_shipping_tokens(count: int = 15) -> list:
    """Усунено дублювання коду та замінено MD5 на безпечний secrets."""
    return [
        {"token": secrets.token_hex(16), "idx": i, "status": "calculated_shipping_rate"}
        for i in range(count)
    ]
