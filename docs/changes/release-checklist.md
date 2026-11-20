---
owner: Vlad8800
status: published
review_date: 2027-02-18
tags: [ops]
---

# Release Checklist — RFC-001

Статус: локальна перевірка, не production release. Go/no-go приймає CCB.

- [ ] Усі цільові та наявні регресійні тести зелені; докази збережені.
- [ ] Міграції: N/A обґрунтовано в Impact Analysis; для майбутньої БД staging drill обов'язковий.
- [ ] Документація, ISD, API addendum, ADR і CHANGELOG оновлені.
- [ ] Реальний моніторинг та доставка алертів перевірені (специфікації недостатньо).
- [ ] Відкат доступний; policy restore drill PASS; немає витоку даних.
- [ ] Підготовлена комунікація про 503/Retry-After і вікно робіт.
- [ ] CCB прийняв результати; budget не вичерпаний або погоджено emergency change.

Production NO-GO до підключення алертів, приймання людиною та перевірки staging.
Результати локальних перевірок: [звіт](../../Lab12/REPORT.md).

Простежуваність: REQ-OPS-001 → RFC-001 → FAIL/PASS Git commits
→ tests/test_lab12_storage_failure.py → CHANGELOG → lab12-local-pass
→ Lab12_QA.zip (SHA256 в окремому manifest). Точні хеші — Lab12/evidence/git-history.json.

Комунікація (підготовлений текст, не надіслано): «Під час тимчасової недоступності
сховища export повертає 503; повторіть запит після Retry-After. Успішні дані не змінюються».
