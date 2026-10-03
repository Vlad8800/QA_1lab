import logging
import secrets
from typing import Any, Dict, List
import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# Конфігурація для Resilience (Завдання 2)
EXTERNAL_TARIFF_API_URL = "http://127.0.0.1:9999/api/v1/tariffs"
FALLBACK_SHIPPING_RATE = 25.0  # Безпечний локальний дефолтний тариф


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


# --- РЕАЛІЗАЦІЯ RESILIENCE PATTERNS (Retry + Backoff) ---
# Захист від Retry Storm: обмежуємо до 3 спроб та збільшуємо інтервал між ними
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.1, min=0.1, max=0.5),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    reraise=True,
)
def _fetch_external_base_rate(country_code: str) -> float:
  """Виклик зовнішньої служби тарифів із таймаутом і повторними спробами."""
  with httpx.Client(timeout=0.5) as client:
    response = client.get(
        f"{EXTERNAL_TARIFF_API_URL}?country={country_code.upper()}"
    )
    response.raise_for_status()
    data = response.json()
    return float(data.get("base_rate", 20.0))


def calculate_shipping_cost(
    country_code: str,
    weight: float,
    is_express: bool,
    customer_tier: str,
    is_holiday: bool,
) -> Dict[str, Any]:
  """Розрахунок вартості доставки зі стійкістю до збоїв (Graceful Degradation)."""
  if country_code.upper() == "UA":
    return {
        "final_cost": 2.0,
        "is_fallback": False,
        "attempts": 1,
        "mode": "domestic",
    }

  # Звернення до зовнішньої залежності з Fallback-механізмом
  is_fallback = False
  attempts = 1
  try:
    base_rate = _fetch_external_base_rate(country_code)
  except Exception as exc:
    # Graceful Degradation: якщо сервіс лежить, використовуємо фіксований локальний тариф
    logger.warning(
        "External tariff service failure (%s). Fallback activated.", exc
    )
    base_rate = FALLBACK_SHIPPING_RATE
    is_fallback = True
    attempts = 3

  if weight > 20.0:
    base_rate += 15.0
  elif weight > 5.0:
    base_rate += 5.0

  if is_express:
    multiplier = 2.0 if customer_tier.lower() == "regular" else 1.5
    holiday_surcharge = 20.0 if is_holiday else 0.0
    final_cost = (base_rate * multiplier) + holiday_surcharge
  else:
    final_cost = base_rate

  return {
      "final_cost": round(final_cost, 2),
      "is_fallback": is_fallback,
      "attempts": attempts,
      "mode": "fallback_applied" if is_fallback else "external_live",
  }

def generate_shipping_tokens(count: int = 3) -> List[Dict[str, str]]:
  """Генерація криптографічно стійких токенів для відстеження посилки."""
  return [
      {
          "token": secrets.token_hex(16),
          "status": "calculated_shipping_rate",
      }
      for _ in range(count)
  ]
def calculate_order_discount(
    customer_type: str,
    total_amount: float,
    items_count: int,
    coupon_code: str | None = None,
    is_holiday: bool = False,
) -> float:
    """
    Початкова складна реалізація для фіксації baseline.
    Cognitive Complexity перевищує 15.
    """
    if total_amount <= 0:
        raise ValueError("Total amount must be positive")

    discount = 0.0

    # Глибока вкладеність для SonarQube S3776
    if customer_type == "vip":
        if total_amount > 500:
            discount += 0.15
        else:
            if total_amount > 200:
                discount += 0.10
            else:
                discount += 0.05
    elif customer_type == "wholesale":
        if items_count >= 10:
            discount += 0.20
        else:
            discount += 0.10
    elif customer_type == "standard":
        if total_amount > 300:
            discount += 0.05
    else:
        discount = 0.0

    if coupon_code is not None:
        if coupon_code == "SAVE10":
            if discount < 0.30:
                discount += 0.10
        elif coupon_code == "SAVE5":
            discount += 0.05

    final_price = total_amount * (1.0 - discount)

    delivery_fee = 0.0
    if final_price < 200:
        delivery_fee = 15.0
        if is_holiday:
            delivery_fee += 10.0

    return final_price + delivery_fee