import secrets

# --- РЕФАКТОРИНГ (ЗАВДАННЯ 4) ---

def _get_international_shipping_surcharge(weight: float, express: bool, is_holiday: bool, is_regular: bool) -> float:
    """Використано техніку Extract Method для ізоляції надбавки."""
    if not express:
        return 30.0 if weight > 20 else 15.0

    if is_regular:
        return 100.0 if is_holiday else 80.0
    return 50.0


def calculate_shipping_cost(country: str, weight: float, express: bool, customer_type: str, is_holiday: bool) -> float:
    """
    Оптимізована функція:
    - Застосовано Guard Clauses для виключення зайвої вкладеності.
    - Cognitive Complexity знижено з 18 до 3.
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
    """Усунено дублювання коду та замінено MD5 на криптографічно безпечний secrets."""
    return [
        {"token": secrets.token_hex(16), "idx": i, "status": "calculated_shipping_rate"}
        for i in range(count)
    ]