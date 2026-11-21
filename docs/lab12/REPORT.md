---
owner: Vlad8800
status: published
review_date: 2027-02-19
tags: [lab12, report, hub]
---
# Звіт з лабораторної роботи №12 (Project Hub)

- **Проєкт:** `Lab12_QA` (`app/export`) | **Автор:** `Vlad8800` | **Дата здачі:** `21.11.2026`
- **Мета:** звести результати експлуатаційного пакету SRE, управління змінами та обробки інциденту `INC-001` (RCA/CAPA) з посиланнями на артефакти й докази.

## 1. Завдання 1 — експлуатаційний пакет SRE

- **Операція:** експорт персональних даних `GET /api/users/{id}/personal-data` та `/api/v1/users/{id}/personal-data`. Специфікацію та опис операцій наведено в [`docs/api/export-operations.md`](../api/export-operations.md).
- **Runbook, алерти та ISD:** регламент відновлення наведено в [`docs/runbooks/RB-001.md`](../runbooks/RB-001.md), правила моніторингу — у [`docs/operations/alerts.md`](../operations/alerts.md), архітектуру розгортання, процедури відновлення та `RTO`/`RPO` — у [`docs/architecture/isd.md`](../architecture/isd.md).
- **Backup та restore drill:** політику копіювання описано в [`docs/operations/backup-policy.md`](../operations/backup-policy.md); перевірку відновлення підтверджено [`scripts/lab12_restore_drill.py`](../../scripts/lab12_restore_drill.py) і [`Lab12/evidence/restore-drill.json`](../../Lab12/evidence/restore-drill.json).
- **SLI / SLO / SLA:** три індикатори, цільові пороги, бюджет помилок і політику його витрачання зафіксовано в [`docs/slo.yaml`](../slo.yaml) та [`docs/operations/service-levels.md`](../operations/service-levels.md).
- **Межі:** локально перевірено відновлення в in-memory контурі; off-site backup і зовнішній Prometheus/Alertmanager є цільовою production-моделлю.

## 2. Завдання 2 — управління змінами

- **Зміна:** перехоплення `OSError` у `app/export/routes.py:81-87` із поверненням `HTTP 503` та `Retry-After: 30` без витоку PII чи діагностики сховища ([`ADR-0003`](../architecture/adr/0003-export-storage-unavailability.md)).
- **Документи змін:** [`RFC-001.md`](../changes/RFC-001.md), [`impact-analysis.md`](../changes/impact-analysis.md), [`CCB-001.md`](../changes/CCB-001.md) та [`release-checklist.md`](../changes/release-checklist.md).
- **Реєстрація та перевірки:** зареєстровано в GitHub Issues ([`RFC-001 #3`](https://github.com/Vlad8800/QA_1lab/issues/3)) та проведено через стани `Draft → Assessment → Pending CCB → Approved → Implemented` у GitHub Project ([`tracker.json`](../../Lab12/evidence/tracker.json), [`rfc-state-history.json`](../../Lab12/evidence/rfc-state-history.json)); локально пройдено `pytest`, `markdownlint-cli2` і `mkdocs build --strict`.

## 3. Завдання 3 — інцидент, RCA/CAPA та супровід

- **Артефакти:** картка інциденту [`INC-001.md`](../incidents/INC-001.md), документація legacy-компонента [`export-component.md`](../legacy/export-component.md) ([`legacy-analysis.json`](../../Lab12/evidence/legacy-analysis.json)), фінальний робочий аркуш [`INC-001-rca-workbook.md`](../incidents/INC-001-rca-workbook.md) та [`maintenance-plan.md`](../maintenance-plan.md).
- **Докази:** інцидент є контрольованою локальною симуляцією (`TestClient` + `unittest.mock`), а не production-аварією. Результати зафіксовано у [`FAIL.json`](../../Lab12/evidence/FAIL.json), [`PASS.json`](../../Lab12/evidence/PASS.json), [`regression-FAIL.log`](../../Lab12/evidence/regression-FAIL.log), [`regression-PASS.log`](../../Lab12/evidence/regression-PASS.log) та комітах `641ff03` → `7c16651` → `402f83a`.

## 4. Валідація та межі

- **Фактичні результати:** до виправлення — 5 відповідей `HTTP 500` (`FAIL.json`); після патчу — 5 відповідей `HTTP 503` із `Retry-After: 30` і `pii_in_error: false` та `[200, 200, 200]` після відновлення (`PASS.json`), `regression-PASS.log`, `restore-drill.json`.
- **Межі:** відсутні production-інфраструктура та фізична БД; типізований виняток `StorageUnavailableError` для `TimeoutError` у всіх методах читання заплановано в `PA-01` до `2026-11-28`.

## 5. Використання ШІ

- **Лог та валідація:** [`Lab12/AI_VALIDATION.md`](../../Lab12/AI_VALIDATION.md) містить повний лог діалогу з ШІ та перелік перевірених артефактів.
- **Розмежування:** ШІ допоміг розібрати вимоги, звірити рядки коду й форматування; аналіз «5 Чому», діаграму Ісікави, картки CAPA та перевірку доказів виконано самостійно.
