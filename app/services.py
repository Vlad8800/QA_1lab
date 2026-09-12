import hashlib

# --- СИМУЛЯЦІЯ ДЕГРАДАЦІЇ ЯКОСТІ ДЛЯ СТАНУ FAIL ---

def bad_calculate_complex_shipping(country, weight, express, customer_type, is_holiday):
    """Штучне порушення: Cognitive Complexity > 15 через 5 рівнів вкладеності."""
    cost = 10.0
    if country != "UA":
        if weight > 5:
            if express:
                if customer_type == "regular":
                    if is_holiday:
                        cost += 100
                    else:
                        cost += 80
                else:
                    cost += 50
            else:
                if weight > 20:
                    for i in range(3):
                        if i == 2:
                            cost += 30
                else:
                    cost += 15
        else:
            cost += 5
    else:
        cost = 2.0
    return cost


def duplicate_shipping_one():
    """Штучне дублювання коду та MD5 (Security Issue)."""
    data = []
    for i in range(15):
        val = (i * 42) / 3.14
        h = hashlib.md5(str(val).encode()).hexdigest()
        data.append({"token": h, "idx": i, "status": "calculated_shipping_rate"})
    return data


def duplicate_shipping_two():
    """1-в-1 дублікат для перевищення ліміту Duplicated Lines %."""
    data = []
    for i in range(15):
        val = (i * 42) / 3.14
        h = hashlib.md5(str(val).encode()).hexdigest()
        data.append({"token": h, "idx": i, "status": "calculated_shipping_rate"})
    return data