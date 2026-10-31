# Лабораторна робота 7 — завдання 3

## Хмарний моніторинг складності та карта Hotspots

**Об'єкт:** репозиторій `QA_1lab`, прикладний Python-код і його Git-історія.  
**Метод збору історії:** ретроспективний аудит, варіант 1. Репозиторій уже має 47 комітів.  
**Період:** останні 90 днів від моменту запуску.  
**Зріз локального запуску:** 31.10.2026; Git HEAD `2fb24e2`.  
**Сканер:** Radon 6.0.1, метрики McCabe CC і Halstead Effort.

### 1. Автоматизація в GitHub Actions

Файл [`.github/workflows/lab7-hotspots.yml`](../../.github/workflows/lab7-hotspots.yml) запускається на кожен push і pull request. Job працює в Docker-образі `python:3.11-bookworm`, встановлює Git і Radon, забирає повну історію (`fetch-depth: 0`), сканує всі відстежувані Python-файли та прикріплює п'ять файлів як build artifact. Повний лістинг:

```yaml
name: Lab 7 Hotspots

on:
  push:
  pull_request:

jobs:
  hotspots:
    runs-on: ubuntu-latest
    container:
      image: python:3.11-bookworm
    permissions:
      contents: read
    steps:
      - name: Install Git in container
        run: apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

      - name: Check out complete history
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Trust checked-out repository in container
        run: git config --global --add safe.directory "$GITHUB_WORKSPACE"

      - name: Install complexity scanner
        run: python -m pip install --no-cache-dir radon==6.0.1

      - name: Scan repository and calculate 90-day churn
        run: python scripts/build_hotspots.py --output-dir artifacts/hotspots

      - name: Upload structured reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: lab7-hotspots-${{ github.run_id }}
          path: artifacts/hotspots/
          if-no-files-found: error
          retention-days: 30
```

Файл [`scripts/build_hotspots.py`](../../scripts/build_hotspots.py) виконує оркестрацію. Він використовує `git ls-files` для точного набору вихідних файлів, викликає `radon cc -j -s` та `radon hal -j`, підраховує кількість комітів для кожного файлу і з'єднує результати за шляхом. Виходи: `radon_cc.json`, `radon_halstead.json`, `hotspots.json`, `hotspots.csv`, `churn_90d.txt`.

### 2. Реальний Git churn

Еквівалент консольної команди для перегляду історії:

```bash
git log --since='90 days ago' --no-renames --format= --name-only -- '*.py' | sed '/^$/d' | sort | uniq -c | sort -nr
```

У скрипті використано ту саму команду з `-z` для коректної обробки назв файлів з пробілами. Підрахунок обмежено поточними відстежуваними Python-файлами. Вивід локального запуску, відсортований за кількістю комітів:

```text
 18  app/services.py
  9  tests/test_main.py
  7  app/main.py
  4  audit_halstead_mccabe.py
  3  tests/test_services.py
  2  demo_infra_reliability_stability.py
  1  app/privacy/sanitizer.py
  1  app/privacy/filter.py
  1  app/anonymization/service.py
  1  app/export/service.py
  1  app/privacy/formatter.py
```

Повний список 47 файлів є у [`churn_90d.txt`](task3-artifacts/churn_90d.txt).

### 3. Правило класифікації

Складність файлу — **максимальний CC окремої функції або методу** з Radon, а не сума CC всіх функцій. Висока складність: `max CC > 10`; висока мінливість: `>= 5` комітів за 90 днів. Поріг churn — явне локальне правило для цього репозиторію. Halstead Effort збережено як додаткову ознаку, щоб при однаковому CC розрізняти обсяг алгоритмічної роботи.

| CC | Churn | Категорія | Рішення |
|---|---|---|---|
| > 10 | >= 5 | Hotspot | Перший пріоритет для рефакторингу та регресійних тестів |
| > 10 | < 5 | Sleeping Danger | Рефакторинг перед наступною зміною функціональності |
| <= 10 | >= 5 | Active Development | Контроль тестів і тенденції складності |
| <= 10 | < 5 | Stable Code | Звичайний моніторинг |

### 4. Синергетична матриця прикладного коду

Дані нижче отримано з [`hotspots.json`](task3-artifacts/hotspots.json), [`radon_cc.json`](task3-artifacts/radon_cc.json) і Git CLI, а не оцінено вручну.

| Файл | Max CC | Halstead Effort | Комітів 90 днів | Категорія |
|---|---:|---:|---:|---|
| `app/services.py` | 6 | 2857.98 | 18 | Active Development |
| `app/main.py` | 4 | 11.61 | 7 | Active Development |
| `app/privacy/sanitizer.py` | 18 | 3346.72 | 1 | Sleeping Danger |
| `app/privacy/filter.py` | 15 | 440.70 | 1 | Sleeping Danger |
| `app/anonymization/service.py` | 11 | 2112.78 | 1 | Sleeping Danger |
| `app/export/service.py` | 11 | 156.28 | 1 | Sleeping Danger |
| `app/privacy/formatter.py` | 11 | 93.21 | 1 | Sleeping Danger |
| `app/consent/gate.py` | 8 | 646.11 | 1 | Stable Code |
| `app/export/routes.py` | 7 | 161.96 | 1 | Stable Code |
| `app/privacy/middleware.py` | 6 | 153.77 | 1 | Stable Code |

**Висновок для наступного спринту.** Справжніх Hotspots за обраними порогами немає: жоден файл одночасно не має CC > 10 і щонайменше 5 змін. Найбільший майбутній ризик — `app/privacy/sanitizer.py` (CC 18, Effort 3346.72) і `app/privacy/filter.py` (CC 15). Їх варто розбити на менші функції й додати адресні тести **перед** новими змінами в приватності. `app/services.py` змінювався 18 разів, але максимальний CC лишається 6; його не слід оголошувати червоним лише через churn. Для нього пріоритет — регресійні тести доставки та контроль росту CC на наступних pull request. Малозмінювані файли з CC <= 10 залишаються у звичайному моніторингу.

Ця матриця показує поточний стан, а не причинність дефектів. Один коміт рахується один раз для кожного згаданого файлу; перейменування обліковується як новий шлях (`--no-renames`). Показники оновлюються на кожному запуску CI.

### 5. Перевірка

Локально сканер успішно обробив 47 відстежуваних Python-файлів і створив усі п'ять звітів у [`task3-artifacts`](task3-artifacts). Хмарний статус і посилання на artifact потрібно додати після запуску workflow у GitHub Actions; локальний запуск не є доказом `Job Success` у хмарі.
