# Project Hub Лабораторна робота 7

**Дисципліна:** Інженерія якості та супровід програмних систем  
**Виконавець:** Лазарєв В. В., група 441  
**Дата:** 31 жовтня 2026 року  
**Об'єкт:** метод `calculate_shipping_cost` і репозиторій [QA_1lab](https://github.com/Vlad8800/QA_1lab).

## Матеріали

- [Повний звіт завдань 1 і 2](https://github.com/Vlad8800/QA_1lab/blob/main/docs/lab7/Звіт%20лабораторна%207.md)
- [Повний звіт завдання 3](https://github.com/Vlad8800/QA_1lab/blob/main/docs/lab7/Завдання%203%20Hotspots.md)
- [Код аудиту Чепіна](https://github.com/Vlad8800/QA_1lab/blob/main/audit_chapin.py), [код сервісу](https://github.com/Vlad8800/QA_1lab/blob/main/app/services.py), [тести](https://github.com/Vlad8800/QA_1lab/blob/main/tests/test_services.py)
- [GitHub Actions](https://github.com/Vlad8800/QA_1lab/blob/main/.github/workflows/lab7-hotspots.yml), [скрипт метрик](https://github.com/Vlad8800/QA_1lab/blob/main/scripts/build_hotspots.py), [JSON і CSV](https://github.com/Vlad8800/QA_1lab/tree/main/docs/lab7/task3-artifacts)
- [Успішна збірка Hotspots з артефактом](https://github.com/Vlad8800/QA_1lab/actions/runs/41207861471), [скріншот](https://github.com/Vlad8800/QA_1lab/blob/main/docs/lab7/github-actions-success.png), [SonarCloud і 50 тестів](https://github.com/Vlad8800/QA_1lab/actions/runs/41207861463)

## Завдання 1 Інформаційний аудит

Історичний варіант методу після лабораторної 6 має McCabe CC = 1. Бізнес-рішення винесено в таблиці, тому простий граф керування приховує багато селекторів даних. У вихідній матриці Чепіна класи P/M/C/T мають кількості 5/1/8/1 і ваги 1/2/3/0,5. Розрахунок: 5 + 2 + 24 + 0,5 = **31,5**. [Повна таблиця з роллю кожної змінної](https://github.com/Vlad8800/QA_1lab/blob/main/docs/lab7/Звіт%20лабораторна%207.md).

Класифікацію `final_cost` як M треба захистити усно: виклик `round(final_cost, 2)` не перезаписує локальну змінну. Це відкрите питання семантичного аудиту, а не результат автоматичного сканера.

## Завдання 2 FAIL і PASS

У [коміті FAIL](https://github.com/Vlad8800/QA_1lab/commit/3aa6677) вартість святкової доставки помилково перезаписувалася значенням 12,0 замість очікуваних 70,0. У [коміті PASS](https://github.com/Vlad8800/QA_1lab/commit/2fb24e2) введено `ShippingOrderSpec` і `ShippingRateResult` як `@dataclass(frozen=True)`. Тест перевіряє фінансовий результат і виняток `FrozenInstanceError` при спробі змінити поля. За вихідною матрицею Чепіна індекс знизився з **31,5 до 5,5**, тобто у **5,73 раза**.

## Завдання 3 Hotspots

Workflow працює на push і pull request у Docker, встановлює Radon 6.0.1, сканує всі відстежувані Python-файли, рахує кількість комітів за 90 днів і публікує JSON/CSV як артефакт. Висока складність визначена як max CC > 10, висока мінливість — щонайменше 5 комітів. Локальний зріз на коміті `2e2235c` охопив 48 файлів.

| Файл | Max CC | Комітів за 90 днів | Категорія |
|---|---:|---:|---|
| `app/services.py` | 6 | 19 | Active Development |
| `app/main.py` | 4 | 7 | Active Development |
| `app/privacy/sanitizer.py` | 18 | 1 | Sleeping Danger |
| `app/privacy/filter.py` | 15 | 1 | Sleeping Danger |
| `app/anonymization/service.py` | 11 | 1 | Sleeping Danger |
| `app/export/service.py` | 11 | 1 | Sleeping Danger |
| `app/privacy/formatter.py` | 11 | 1 | Sleeping Danger |
| `app/consent/gate.py` | 8 | 1 | Stable Code |

За цими порогами червоних Hotspots немає. Перед наступними змінами у приватності пріоритет — адресні тести та спрощення складних функцій у `sanitizer.py` і `filter.py`. Для часто змінюваного `services.py` пріоритет — регресійні тести й контроль росту CC.

## Перевірка

```powershell
.\.venv-1\Scripts\python.exe audit_chapin.py
.\.venv-1\Scripts\python.exe -m radon cc app\services.py -s
git show 3aa6677:app/services.py
git show 2fb24e2:app/services.py
.\.venv-1\Scripts\python.exe scripts\build_hotspots.py --output-dir artifacts\hotspots
Get-Content artifacts\hotspots\hotspots.csv
```

## Протокол використання ШІ

Код, аналітику та оформлення підготовлено за допомогою Codex. Перевірено історичні коміти FAIL/PASS, CC поточного методу, генерацію структурованих звітів, артефакт GitHub Actions і 50 тестів у хмарі. Перед захистом студенту слід самостійно перевірити класифікацію змінних, пояснити ваги P/M/C/T та продемонструвати запуск команд.
