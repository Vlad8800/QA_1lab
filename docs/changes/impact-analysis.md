---
owner: Vlad8800
status: published
review_date: 2027-02-18
tags: [ops]
---

# Impact Analysis RFC-001: сім рівнів

| Рівень | Конкретний вплив та перевірка |
| --- | --- |
| Вимоги | REQ-OPS-001, сценарій авторизованого export під час відмови; README та опис сервісу |
| Архітектура | routes → service → repository; HTTP boundary переводить OSError у 503; новий ADR-0003 |
| Код | app/export/routes.py; tests/test_lab12_storage_failure.py; scripts/lab12_incident.py |
| API | GET /api/users/{id}/personal-data та /api/v1/users/{id}/personal-data; additive опис 503; поля успішної відповіді незмінні; клієнти мають обробляти 503/Retry-After |
| Дані | Зміни схеми відсутні, SQL-міграція N/A; модель in-memory; перезапуск може втратити зміни, тому не є автоматичним обходом |
| Тести | export, IDOR 401/403, privacy logging, unavailable repository для обох шляхів, recovery 200, contract shapes |
| Документація й експлуатація | RB-001, alerts, slo.yaml, ISD, ADR-0003, API operational addendum, CHANGELOG, maintenance plan |

Breaking changes не вводяться: міграційний гайд не потрібний, але новий retry-код треба
пояснити інтеграторам. Наявний curated OpenAPI ЛР11 описує лише частину API;
export документується окремим additive фрагментом, а не вигаданим повним контрактом.
Risk Exposure = 2 × 3 = 6/25; ризик витоку мінімізується загальною помилкою без str(exc).
За наявності витоку — no-go незалежно від сумарного бала.
