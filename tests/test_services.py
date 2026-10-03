import pytest
from app.services import calculate_order_discount


def test_standard_customer_small_order():
    """Стандартний клієнт, мала сума: без знижки + базова доставка 15."""
    result = calculate_order_discount(
        customer_type="standard",
        total_amount=100.0,
        items_count=2,
        coupon_code=None,
        is_holiday=False,
    )
    # 100.0 - 0% + 15.0 = 115.0
    assert result == 115.0


def test_standard_customer_large_order():
    """Стандартний клієнт > 300: знижка 5%, безкоштовна доставка (>200)."""
    result = calculate_order_discount(
        customer_type="standard",
        total_amount=400.0,
        items_count=3,
        coupon_code=None,
        is_holiday=False,
    )
    # 400.0 * 0.95 = 380.0
    assert result == 380.0


def test_invalid_order_amount_raises_error():
    """Граничний випадок: недопустима сума викликає помилку ValueError."""
    with pytest.raises(ValueError, match="Total amount must be positive"):
        calculate_order_discount(
            customer_type="standard",
            total_amount=-10.0,
            items_count=1,
            coupon_code=None,
            is_holiday=False,
        )


def test_vip_customer_with_coupon_and_free_delivery():
    """VIP клієнт > 500 (15%) + купон SAVE10 (10%) = 25% знижки."""
    result = calculate_order_discount(
        customer_type="vip",
        total_amount=600.0,
        items_count=5,
        coupon_code="SAVE10",
        is_holiday=False,
    )
    # 600.0 * (1 - 0.25) = 450.0
    assert result == 450.0


def test_wholesale_bulk_order():
    """Оптовий клієнт (>= 10 позицій): знижка 20%."""
    result = calculate_order_discount(
        customer_type="wholesale",
        total_amount=1000.0,
        items_count=15,
        coupon_code=None,
        is_holiday=False,
    )
    # 1000.0 * 0.80 = 800.0
    assert result == 800.0


def test_small_order_holiday_delivery():
    """Святкова доставка для малого замовлення: 15 base + 10 holiday = 25."""
    result = calculate_order_discount(
        customer_type="standard",
        total_amount=50.0,
        items_count=1,
        coupon_code=None,
        is_holiday=True,
    )
    # 50.0 + (15.0 + 10.0) = 75.0
    assert result == 75.0


def test_coupon_save10_discount_limit():
    """Купон SAVE10 блокується, якщо поточна знижка вже досягла 30%."""
    result = calculate_order_discount(
        customer_type="wholesale",
        total_amount=2000.0,
        items_count=20,
        coupon_code="SAVE5",
        is_holiday=False,
    )
    # 20% wholesale + 5% SAVE5 = 25%
    # 2000.0 * 0.75 = 1500.0
    assert result == 1500.0