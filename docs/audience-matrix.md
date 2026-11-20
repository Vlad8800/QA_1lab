---
owner: Vlad8800
status: published
review_date: 2027-05-19
tags: [architecture]
---

# Матриця покриття аудиторій

Дата: 15.11.2026. Власник документації навчальної поставки: maintainer `Vlad8800`. Чотири аудиторії: розробники (включно з новачком), QA, DevOps, бізнес. Статус **«покрито» означає наявність перевірюваної документальної відповіді**, а не реалізацію всіх production-механізмів.

| Аудиторія | Ключове питання | Документ-відповідь | Статус |
|---|---|---|---|
| Розробники / новачок | Як установити залежності й отримати перший результат локально? | [README quick start](index.md#quick-start-для-windows-powershell), [ISD environments](isd.md#environments) | Покрито: створено README, явні server/test dependencies, UA smoke=52 |
| Розробники | З якими компонентами взаємодіє мій модуль і де він розгортається? | [SDD component map](sdd.md#component-map), component sections → ISD deployment map | Покрито: усі дев’ять компонентів мають взаємні посилання й deployment entry |
| Розробники | Чому залишені RAM-storage та frozen DTO і як змінювати рішення? | [ADR index](architecture/adr/README.md), [0001](architecture/adr/0001-demo-in-memory-boundary.md), [0002](architecture/adr/0002-immutable-shipping-contracts.md) | Покрито: альтернативи, наслідки, дата й supersession policy |
| QA | Де контракти HTTP, внутрішніх викликів, результати та помилки? | [SDD HTTP](sdd.md#http-contracts), [internal](sdd.md#internal-contracts) | Покрито: route/schema/error matrix з нюансами реалізації |
| QA | Як повторити тести, fallback, IDOR та grant/revoke сценарії? | [README tests](index.md#тести-та-вимірювання), [SDD verification](sdd.md#verification) | Покрито: команди та прив’язка до наявних тестів |
| QA | Які гарантії не реалізовані й як трактувати історичні числа? | [SDD security boundaries](sdd.md#security-boundaries), [звіт ЛР10](lab10/task2-report.md) | Покрито: demo principal, RAM, неатомарність, межі повторної перевірки |
| DevOps | Де працює система, які параметри справді читаються? | [ISD environments](isd.md#environments), [configuration](isd.md#configuration) | Покрито: dev/test/production target; legacy env не видається за чинний конфіг |
| DevOps | Які тригери CI/стадії/Quality Gates і як відкотити реліз? | [ISD tooling](isd.md#tooling), [release and rollback](isd.md#release-and-rollback) | Покрито: реальні workflows; відокремлено класифікацію Hotspots від blocking gate |
| DevOps | Як відновити код/стан і які RTO/RPO? | [ISD recovery](isd.md#recovery-objectives), [monitoring](isd.md#monitoring) | Покрито: runbook коду; явно описана втрата RAM; production 60/15 хв — цілі, а не реалізований SLA |
| Бізнес / викладач | Що система робить і для кого? | [README](index.md), [SDD purpose](sdd.md#purpose) | Покрито: сценарії замовлення й даних, навчальне призначення |
| Бізнес / викладач | Як поводиться доставка при відмові зовнішнього сервісу? | [SDD tariff](sdd.md#tariff), [HTTP contracts](sdd.md#http-contracts) | Покрито: fallback 25, ознака режиму, не гарантія правильності external quote |
| Бізнес / викладач | Що потрібно до роботи з реальними користувачами та що підтверджено? | [ISD production](isd.md#production), [SDD boundaries](sdd.md#security-boundaries), [task2 report](lab10/task2-report.md) | Покрито: production-ризики й цілі відділено від наявної реалізації |

## Review after crash test

last_review: 2026-11-15. Для новачка й бізнесу нова поведінка та шлях GET /api/v1/shipping/policy описані в README; розробники/QA отримали [компонент і контракт](sdd.md#shipping-policy); DevOps — [provision-before-API](isd.md#shipping-policy). Усі 12 питань вище знову мають відповідь. Додаткове питання бізнесу про застосовану версію політики покриває новий endpoint. Деталі [FAIL/PASS](lab10/task3-report.md).

Практично закриті прогалини аудиту №1: відсутній README → створено; розрізнені модулі → карта SDD; неописаний запуск/CI → ISD; відсутність пояснень рішень → два ADR; відсутність ролей і маршруту читання → ця матриця та онбординг README. Старі звіти залишаються історичними доказами й не підміняють поточний паспорт.
