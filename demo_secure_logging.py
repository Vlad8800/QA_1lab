"""
Live Demo Script for Laboratory Work #4 - Task 1: Secure Logging & PII Masking.
Run this script to demonstrate all 4 requirements in 5 seconds to the instructor.
"""
import json
import logging
import uuid
from app.privacy import (
    setup_privacy_logging,
    set_correlation_id,
    sanitize_text,
    sanitize_data,
)

def run_demo():
    print("=" * 70)
    print(" ДЕМОНСТРАЦІЯ ЗАВДАННЯ 1: SECURE LOGGING ТА МАСКУВАННЯ PII (LAB #4)")
    print("=" * 70)

    # 1. Текстове маскування
    print("\n--- [1] МАСКУВАННЯ ЗВИЧАЙНОГО ТЕКСТУ (Plain Text) ---")
    raw_text = (
        "Користувач ivan.petrenko@corp.ua (тел: +380501234567) увійшов у систему "
        "з паролем password=SecretPass!2026 та токеном Bearer eyJhbGciOiJIUzI1NiJ9.test"
    )
    print("ВХІДНЕ ПОВІДОМЛЕННЯ (RAW):")
    print(f"  {raw_text}")
    print("\nОЧИЩЕНЕ ПОВІДОМЛЕННЯ (SANITIZED):")
    print(f"  {sanitize_text(raw_text)}")

    # 2. Структурований JSON-лог
    print("\n--- [2] СТРУКТУРОВАНИЙ JSON-ЛОГ З CORRELATION ID ---")
    setup_privacy_logging(log_level=logging.INFO, json_format=True)
    logger = logging.getLogger("app.demo")

    cid = f"demo-req-{uuid.uuid4().hex[:8]}"
    set_correlation_id(cid)

    print(f"Згенеровано Correlation ID: {cid}")
    print("Логування події замовлення з чутливими extra-даними...")

    # Емулюємо подію з вкладеним DTO
    logger.info(
        "Order payment initiated",
        extra={
            "event_type": "PAYMENT_INITIATED",
            "actor_id": "usr_9981",
            "email": "customer.buyer@shop.com",
            "phone": "+380679876543",
            "payment_details": {
                "card_number": "4111222233334444",
                "cvv": "999",
                "api_key": "YOUR_SYNTHETIC_KEY",  # gitleaks:allow      
            }
        }
    )

    # 3. Маскування у винятках (Exception & Traceback)
    print("\n--- [3] МАСКУВАННЯ У ПОВІДОМЛЕННЯХ ПОМИЛОК ТА TRACEBACK ---")
    try:
        raise ValueError(
            "Помилка автентифікації для user=admin.support@system.ua з паролем password='SuperAdminPass123!'"
        )
    except Exception:
        logger.exception("Зловмисна або аварійна спроба автентифікації перехоплена")

    print("\n" + "=" * 70)
    print(" Всі PII частково замасковані, секрети замінено на [REDACTED],")
    print(" технічні дані (Correlation ID, timestamp, status) повністю збережено.")
    print("=" * 70)

if __name__ == "__main__":
    run_demo()

