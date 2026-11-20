---
owner: Vlad8800
status: published
review_date: 2027-02-18
tags: [ops]
---

# Локальний запуск

Python 3.11–3.12, Node.js 22+, Git; для генерації SDK — Java 17+ або пакет jdk4py.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-docs.txt uvicorn
New-Item -ItemType Directory runtime -Force
Copy-Item config/shipping-policy.example.json runtime/shipping-policy.json
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

В іншому терміналі з кореня репозиторію:

```powershell
npm install
npm run lint:api
npm run lint:md
python scripts/check_review_dates.py
python -m mkdocs build --strict
python -m mkdocs serve -a 127.0.0.1:8001
```

API: <http://127.0.0.1:8000/docs>; база знань: <http://127.0.0.1:8001>.
Політика доставки читається до старту; файл runtime не комітиться.
Дозволені CORS origins задаються через DOCS_CORS_ORIGINS (через кому, без секретів).
Для Swagger на GitHub Pages виберіть HTTP localhost server і дозвольте браузеру доступ до локальної мережі, якщо він запитає.

[[architecture/isd|Середовища]] · [[architecture/sdd|Компоненти]]
