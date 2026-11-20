---
owner: Vlad8800
status: published
review_date: 2027-02-18
tags: [ops]
---

# QA_1lab — Order Quality & Resilience

Навчальний FastAPI-проєкт: розрахунок замовлень і доставки, керування згодами,
експорт та анонімізація демонстраційних даних. Стан зберігається в пам’яті процесу.

## Швидкий старт

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt uvicorn
New-Item -ItemType Directory runtime -Force
Copy-Item config/shipping-policy.example.json runtime/shipping-policy.json
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API: <http://127.0.0.1:8000/docs>.
Політика доставки: GET /api/v1/shipping/policy.
Маршрут новачка: [локальне середовище](docs/developer/local.md) → [SDD](docs/architecture/sdd.md)
→ [контракти](docs/api/index.md) → [внесення змін](CONTRIBUTING.md).
[Сайт документації](https://Vlad8800.github.io/QA_1lab/) — ціль публікації GitHub Pages.

## Definition of Done

| Об’єкт | Обов’язкова перевірка |
| --- | --- |
| Контракти | Spectral та live contract tests |
| Markdown | markdownlint |
| Посилання, nav | mkdocs build --strict |
| Актуальність | owner / status / review_date, check_review_dates.py |
| Публічна поведінка | docs/ + OpenAPI + CHANGELOG + рев’ю власника |

## Лабораторна 11

[Звіт](Lab11/REPORT.md), [докази запусків](Lab11/evidence/), [сценарій захисту](Lab11/DEMO.md).
