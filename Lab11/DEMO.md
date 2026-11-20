---
owner: Vlad8800
status: draft
review_date: 2027-02-18
tags: [ops]
---

# ЛР11 — запуск і демонстрація

1. Відкрити корінь QA_1lab у VS Code. Виконати команди з `docs/developer/local.md`.
2. Запустити API на `127.0.0.1:8000`; відкрити `http://127.0.0.1:8000/contract-docs`.
   Це API-first Swagger із `docs/api/openapi.yaml`. `/docs` залишається автоматичною code-first довідкою FastAPI.
3. Виконати `python scripts/run_lab11_checks.py`. Для кожної перевірки зберігається лог у `Lab11/evidence/`.
4. Запустити `python -m mkdocs serve -a 127.0.0.1:8001`, відкрити API → Try it out → Execute.
5. Згенерувати SDK локально: `powershell -File scripts/generate_sdk.ps1` (потрібна Java 17+).
6. Відкрити корінь як Obsidian Vault → Graph view. Перевірити SDD ↔ ISD ↔ ADR ↔ Developer Docs і зробити справжній скріншот.

## Обов’язкове завершення strict-експерименту

Наявні FAIL/PASS-коміти підтверджують локальний аудит посилань. Вони не є доказом запуску MkDocs або GitHub Actions.

Після успішного встановлення залежностей та чистого baseline виконайте:

```shell
python -m mkdocs build --strict
python scripts/crash_test_docs.py
```

Скрипт створює нові FAIL/PASS-коміти та зберігає реальні strict-логи. Git-дерево перед стартом має бути чистим.
Якщо є власні незакомічені зміни, спочатку перегляньте і збережіть їх; не застосовуйте reset/clean.

Для червоного й зеленого Job потрібно відправити спочатку FAIL, а після завершення його перевірки — PASS у гілку `lab11-documentation-as-code`.
Після успішного рев’ю та злиття до main workflow публікує сайт. У Settings → Pages потрібно вибрати GitHub Actions.
Збережіть фактичні скріншоти Job, Swagger, MkDocs та Obsidian у `Lab11/evidence/screenshots/`.

## Що пояснити на захисті

- SSOT: Swagger і SDK читають один openapi.yaml, а не незалежні копії схем.
- API-first: контракт узгоджують до зміни реалізації; code-first: контракт отримують із коду.
- Strict build: warning стає помилкою; orphan-контроль явно увімкнено через validation.nav.omitted_files.
- CODEOWNERS призначає власника; фізичну заборону merge додають Rulesets і required checks.
- review_date — наступний перегляд, а git-revision-date — дата фактичного останнього редагування.
