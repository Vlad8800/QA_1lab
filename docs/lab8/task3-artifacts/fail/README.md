# Контрольований FAIL — каскад успадкування

У найвищому класі `BaseShippingQuote` метод `quote` отримав новий обов'язковий іменований параметр `policy_context`. Дочірні класи `RegionalShippingQuote` та `ExpressHolidayShippingQuote` продовжили викликати `super().quote(spec, base_rate)` за старим контрактом. Той самий збій дійшов до HTTP-маршруту `/api/v1/orders/quote-with-policy`.

[`pytest.log`](pytest.log) містить повний traceback `ExpressHolidayShippingQuote → RegionalShippingQuote → BaseShippingQuote`, помилку `TypeError: ... missing 1 required keyword-only argument: 'policy_context'` і підсумок **3 failed, 53 passed**. Локальний domestic-сценарій не викликає `super().quote`, тому продовжив працювати. [`result.txt`](result.txt) фіксує код завершення 1.

Це навмисний проміжний стан, зафіксований окремим комітом; фінальний PASS має усунути залежність нащадків від успадкованої сигнатури.
