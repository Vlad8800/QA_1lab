"""
Automated Ned Chapin Information-Semantic Complexity Audit Engine (Lab #7).
Covers:
- Task 1: Semantic Audit of Baseline / Unrefactored Method (C_ch = 31.5)
- Task 2: Comparative Verification of Refactored Clean Code (Immutable Value Objects, C_ch = 5.5 <= 6.0)
"""
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass(frozen=True)
class VariableAudit:
    name: str
    var_type: str
    chapin_class: str  # 'C', 'M', 'P', 'T'
    role_description: str
    weight: float


def get_task1_variables() -> List[VariableAudit]:
    return [
        VariableAudit("country_code", "str", "P", "Вхідний аргумент; перетворюється на country_upper та прокидається у rate_source; за правилом P > T класифікується як P", 1.0),
        VariableAudit("weight", "float", "C", "Вхідний аргумент; аргумент bisect_right, що керує вибором індексу діапазону вагової надбавки (селектор гілки)", 3.0),
        VariableAudit("is_express", "bool", "C", "Вхідний аргумент; елемент кортежу-ключа EXPRESS_RATE_LOOKUP, що керує бізнес-правилом надбавки", 3.0),
        VariableAudit("customer_tier", "str", "C", "Вхідний аргумент; елемент кортежу-ключа EXPRESS_RATE_LOOKUP, що визначає ціновий мультиплікатор клієнта", 3.0),
        VariableAudit("is_holiday", "bool", "C", "Вхідний аргумент; елемент кортежу-ключа EXPRESS_RATE_LOOKUP, що активує святкову надбавку", 3.0),
        VariableAudit("country_upper", "str", "C", "Локальна змінна; ключ словників тарифів, формули вартості та режиму; керує вибором алгоритму виконання", 3.0),
        VariableAudit("rate_source", "Callable", "C", "Локальна змінна; зберігає функціональний покажчик на стратегію тарифу; керує диспетчеризацією виклику", 3.0),
        VariableAudit("base_rate", "float", "P", "Локальна змінна; базова ставка, розпакована з тарифу; пасивний числовий операнд розрахунку", 1.0),
        VariableAudit("is_fallback", "bool", "C", "Локальна змінна; прапорець відмовостійкості; виступає ключем FALLBACK_MODE_LOOKUP (пріоритет C > T)", 3.0),
        VariableAudit("attempts", "int", "T", "Локальна змінна; лічильник спроб Tenacity; транзитом без жодних змін передається у вихідний словник", 0.5),
        VariableAudit("weight_surcharge", "float", "P", "Локальна змінна; витягнута надбавка з кортежу; пасивний операнд розрахунку вартості", 1.0),
        VariableAudit("multiplier", "float", "P", "Локальна змінна; розпакований експрес-множник; пасивний операнд розрахунку вартості", 1.0),
        VariableAudit("holiday_fee", "float", "P", "Локальна змінна; розпакована святкова комісія; пасивний операнд розрахунку вартості", 1.0),
        VariableAudit("cost_formula", "Callable", "C", "Локальна змінна; вибрана функціональна формула калькуляції; керує викликом обчислювальної стратегії", 3.0),
        VariableAudit("final_cost", "float", "M", "Локальна змінна; фінансовий результат обчислень, що трансформується/округлюється round(final_cost, 2)", 2.0),
    ]


def get_task2_variables() -> List[VariableAudit]:
    return [
        VariableAudit(
            "spec",
            "ShippingOrderSpec",
            "P",
            "Вхідний аргумент (Immutable Value Object); інкапсулює всі параметри доставки та захищає інваріанти; пасивно читається",
            1.0,
        ),
        VariableAudit(
            "base_rate",
            "float",
            "P",
            "Локальна змінна; базова ставка, отримана від захищеної функції _fetch_shipping_base_rate; числовий операнд",
            1.0,
        ),
        VariableAudit(
            "is_fallback",
            "bool",
            "C",
            "Локальна змінна; статус стійкості, що керує вибором режиму у методі spec.resolve_mode(is_fallback)",
            3.0,
        ),
        VariableAudit(
            "attempts",
            "int",
            "T",
            "Локальна змінна; лічильник спроб, що без змін прокидається у вихідний об'єкт-значення ShippingRateResult",
            0.5,
        ),
    ]


def compute_metrics(variables: List[VariableAudit]) -> Dict[str, Any]:
    p_cnt = sum(1 for v in variables if v.chapin_class == "P")
    m_cnt = sum(1 for v in variables if v.chapin_class == "M")
    c_cnt = sum(1 for v in variables if v.chapin_class == "C")
    t_cnt = sum(1 for v in variables if v.chapin_class == "T")
    c_ch = 1.0 * p_cnt + 2.0 * m_cnt + 3.0 * c_cnt + 0.5 * t_cnt
    return {
        "N": len(variables),
        "P": p_cnt,
        "M": m_cnt,
        "C": c_cnt,
        "T": t_cnt,
        "C_ch": c_ch,
    }


def print_full_audit():
    before_vars = get_task1_variables()
    after_vars = get_task2_variables()
    m_before = compute_metrics(before_vars)
    m_after = compute_metrics(after_vars)

    print("=" * 110)
    print(" ЛАБОРАТОРНА РОБОТА №7 — ПОРІВНЯЛЬНИЙ АУДИТ ЗА ЧЕПІНИМ (ЗАВДАННЯ 1 vs ЗАВДАННЯ 2)")
    print("=" * 110)
    print(f"Об'єкт: calculate_shipping_cost у [app/services.py]")
    print(f"Топологічна складність (McCabe CC): До = 1, Після = 1 (Лінійний код)")
    print("-" * 110)
    print(f"{'ПОКАЗНИК':<35} | {'ДО РЕФАКТОРИНГУ (FAIL)':<25} | {'ПІСЛЯ (IMMUTABLE PASS)':<25} | {'ДИНАМІКА'}")
    print("-" * 110)
    print(f"{'Загальна к-ть змінних (N)':<35} | {m_before['N']:<25} | {m_after['N']:<25} | Зниження на {((m_before['N']-m_after['N'])/m_before['N'])*100:.1f}%")
    print(f"{'Вхідні / пасивні змінні (P)':<35} | {m_before['P']:<25} | {m_after['P']:<25} | Зменшення з 5 до 2")
    print(f"{'Модифіковані змінні (M)':<35} | {m_before['M']:<25} | {m_after['M']:<25} | Повна ліквідація (0!)")
    print(f"{'Керуючі змінні (C)':<35} | {m_before['C']:<25} | {m_after['C']:<25} | Зменшення з 8 до 1")
    print(f"{'Транзитні змінні (T)':<35} | {m_before['T']:<25} | {m_after['T']:<25} | Стабільно 1")
    print("-" * 110)
    print(f"{'Складність Чепіна (C_ch)':<35} | {m_before['C_ch']:<25.1f} | {m_after['C_ch']:<25.1f} | Зниження у {m_before['C_ch']/m_after['C_ch']:.2f} раза (-{((m_before['C_ch']-m_after['C_ch'])/m_before['C_ch'])*100:.1f}%)")
    print(f"{'Норматив Enterprise Clean Code':<35} | {'C_ch <= 10.0':<25} | {'C_ch <= 6.0':<25} | PASS (5.5 <= 6.0)")
    print("=" * 110)


if __name__ == "__main__":
    print_full_audit()
