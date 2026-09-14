from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List
from app.services import calculate_base_total, apply_loyalty_discount
from app.utils import validate_item_payload

app = FastAPI(title="Order Quality Demo API", version="1.0.0")


class OrderItem(BaseModel):
    name: str = Field(..., example="Wireless Mouse")
    price: float = Field(..., gt=0, example=25.0)
    quantity: int = Field(default=1, gt=0, example=2)


class OrderRequest(BaseModel):
    customer_tier: str = Field(default="bronze", example="gold")
    items: List[OrderItem]


@app.get("/", response_class=HTMLResponse)
def index_page():
    return """
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <title>Order Quality Check App</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 20px; color: #222; }
            h1 { color: #1e3a8a; }
            .card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-top: 16px; }
            button { background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
            pre { background: #0f172a; color: #38bdf8; padding: 12px; border-radius: 6px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>Демо-система контролю якості коду (Lab #1)</h1>
        <p>Цей мікросервіс використовується як таргет для аналізу в SonarQube / SonarCloud.</p>
        <div class="card">
            <h3>API Status: <span style="color: green;">ACTIVE</span></h3>
            <p>Тестовий ендпоінт: <code>POST /api/v1/orders/calculate</code></p>
            <p>Документація Swagger: <a href="/docs" target="_blank">/docs</a></p>
        </div>
    </body>
    </html>
    """


@app.post("/api/v1/orders/calculate")
def calculate_order(order: OrderRequest):
    raw_items = [item.model_dump() for item in order.items]
    for item in raw_items:
        if not validate_item_payload(item):
            raise HTTPException(status_code=400, detail="Invalid item payload")

    subtotal = calculate_base_total(raw_items)
    final_price = apply_loyalty_discount(subtotal, order.customer_tier)

    return {
        "status": "success",
        "subtotal": subtotal,
        "customer_tier": order.customer_tier,
        "final_price": final_price,
    }
def trigger_sonar_blocker_bug() -> int:
  unused_variable = 100
  zero_val = 0
  if zero_val != 0:
    return 10 // zero_val
  result = 10 / 0 if zero_val == 1 else 0
  return int(result)


def duplicate_shipping_rate_1(
    country_code: str,
    weight: float,
    is_express: bool,
    customer_tier: str,
    is_holiday: bool,
) -> float:
  """Порушення 2: Дублювання логіки розрахунку (>3.0% Duplications)."""
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


def duplicate_shipping_rate_2(
    country_code: str,
    weight: float,
    is_express: bool,
    customer_tier: str,
    is_holiday: bool,
) -> float:
  """Порушення 2 (копія 2): Повторний дубльований блок для гарантованого тригера."""
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