---
owner: Vlad8800
status: published
review_date: 2027-02-18
tags: [ops]
---

# Export operational addendum

RFC-001 додає 503 з Retry-After=30 для обох export aliases. 401/403/404 і успішна
схема зберігаються. Опис: [OpenAPI fragment](export-operations.yaml).
Це доповнення до curated shipping/policy contract ЛР11, а не повний новий SSOT.
Клієнт має обмежувати retry й не повторювати 401/403 як transient error.
Обробка response models доступна також через code-first /docs локального API.
