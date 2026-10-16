import logging
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.anonymization import anonymization_router
from app.consent import consent_router
from app.export import export_router
from app.privacy import PrivacyLoggingMiddleware, setup_privacy_logging
from app.services import (
    apply_loyalty_discount,
    calculate_base_total,
    calculate_shipping_cost,
)
from app.utils import validate_item_payload

# Initialize centralized privacy-safe logging
setup_privacy_logging()
logger = logging.getLogger("app.orders")

app = FastAPI(
    title="Order Quality & Resilience Demo API",
    version="2.0.0",
    description="API для дослідження продуктивності (SLO) та відмовостійкості (Resilience)",
)

# Attach privacy logging middleware (Correlation ID & audit trails without raw body leaks)
app.add_middleware(PrivacyLoggingMiddleware)

# Attach GDPR personal data export router (Art. 15)
app.include_router(export_router)

# Attach GDPR right to erasure & anonymization router (Art. 17)
app.include_router(anonymization_router)

# Attach GDPR consent management & policy gate router (Art. 6 & Art. 7)
app.include_router(consent_router)


class OrderItem(BaseModel):
    name: str = Field(..., example="Wireless Mouse")
    price: float = Field(..., gt=0, example=25.0)
    quantity: int = Field(default=1, gt=0, example=2)


class OrderRequest(BaseModel):
    customer_tier: str = Field(default="regular", example="gold")
    country_code: str = Field(default="UA", example="PL")
    weight: float = Field(default=1.5, gt=0, example=3.2)
    is_express: bool = Field(default=False, example=True)
    is_holiday: bool = Field(default=False, example=False)
    items: List[OrderItem]


@app.get("/", response_class=HTMLResponse)
def index_page():
    return """
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <title>Order Quality & Resilience App</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 20px; color: #222; }
            h1 { color: #1e3a8a; }
            .card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-top: 16px; }
            pre { background: #0f172a; color: #38bdf8; padding: 12px; border-radius: 6px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>Демо-система контролю якості та стійкості (Lab #2)</h1>
        <p>Мікросервіс для валідації Performance SLO та Fault Injection / Graceful Degradation.</p>
        <div class="card">
            <h3>API Status: <span style="color: green;">ACTIVE</span></h3>
            <p>Тестовий ендпоінт для k6: <code>POST /api/v1/orders/calculate</code></p>
            <p>Документація Swagger: <a href="/docs" target="_blank">/docs</a></p>
        </div>
    </body>
    </html>
    """


@app.post("/api/v1/orders/calculate")
def calculate_order(order: OrderRequest):
    """Повний розрахунок вартості замовлення: валідація, товари, знижка та стійка доставка."""
    logger.info(
        "Order calculation requested",
        extra={
            "event_type": "ORDER_CALCULATION_INIT",
            "country_code": order.country_code,
            "customer_tier": order.customer_tier,
            "items_count": len(order.items),
        }
    )

    raw_items = [item.model_dump() for item in order.items]
    for item in raw_items:
        if not validate_item_payload(item):
            logger.warning(
                "Order calculation rejected due to invalid item payload",
                extra={
                    "event_type": "ORDER_CALCULATION_REJECTED",
                    "status": "validation_failed",
                }
            )
            raise HTTPException(status_code=400, detail="Invalid item payload")

    # 1. Розрахунок вартості товарів замовлення
    subtotal = calculate_base_total(raw_items)
    discounted_price = apply_loyalty_discount(subtotal, order.customer_tier)

    # 2. Розрахунок вартості доставки (зовнішній сервіс із Retry та Fallback)
    shipping_info = calculate_shipping_cost(
        country_code=order.country_code,
        weight=order.weight,
        is_express=order.is_express,
        customer_tier=order.customer_tier,
        is_holiday=order.is_holiday,
    )

    # 3. Підсумкова вартість
    final_total = round(discounted_price + shipping_info["final_cost"], 2)

    logger.info(
        "Order calculation completed successfully",
        extra={
            "event_type": "ORDER_CALCULATION_SUCCESS",
            "status": "success",
            "subtotal": subtotal,
            "final_total": final_total,
        }
    )

    return {
        "status": "success",
        "subtotal": subtotal,
        "discounted_price": discounted_price,
        "shipping": shipping_info,
        "final_total": final_total,
    }