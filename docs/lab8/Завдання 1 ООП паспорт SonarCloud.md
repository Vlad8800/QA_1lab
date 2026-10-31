# Лабораторна робота 8 — завдання 1

## Об'єкт і відтворюваність

- Репозиторій: [`Vlad8800/QA_1lab`](https://github.com/Vlad8800/QA_1lab), гілка `lab8-architecture`.
- Baseline коду: коміт [`8545112`](https://github.com/Vlad8800/QA_1lab/commit/8545112ad2e693517b45ec15ff6c3c03e7438363). Гілку №8 створено без змін вихідного коду з цього коміту.
- Конфігурація сканера: [`sonar-project.properties`](../../sonar-project.properties), `sonar.sources=app`, `sonar.tests=tests`, `sonar.projectKey=Vlad8800_QA_1lab`.
- Сканування SonarCloud цього самого SHA: [успішний запуск SonarCloud Analysis](https://github.com/Vlad8800/QA_1lab/actions/runs/41211784543), аналіз сервера від `2026-10-31T16:48:33+02:00`. Сканер запускала GitHub Actions, а не локальний термінал; локально немає `sonar-scanner` і `SONAR_TOKEN`.
- Сирі відповіді REST API отримано скриптом [`scripts/lab8_fetch_sonar.py`](../../scripts/lab8_fetch_sonar.py) і збережено у [`sonar_api_baseline.json`](task1-artifacts/sonar_api_baseline.json). Аналіз AST/Radon окремо збережено у [`python_oo_estimates.json`](task1-artifacts/python_oo_estimates.json) скриптом [`scripts/lab8_python_oo.py`](../../scripts/lab8_python_oo.py).

Три шари архітектури: `app/services.py` — Core Domain (ціноутворення доставки), `app/export/repository.py` — Infrastructure (сховище даних), `app/consent/schemas.py` — Utility/DTO (схеми обміну).

## Декларація виконаних HTTP-запитів

Публічний проєкт дозволяє ці запити без токена. Команда відтворення у PowerShell з кореня репозиторію:

```powershell
.\.venv-1\Scripts\python.exe scripts\lab8_fetch_sonar.py
```

Скрипт виконав:

```text
GET https://sonarcloud.io/api/metrics/search?ps=500
GET https://sonarcloud.io/api/project_analyses/search?project=Vlad8800_QA_1lab&ps=1
GET https://sonarcloud.io/api/measures/component?component=Vlad8800_QA_1lab&metricKeys=complexity%2Ccognitive_complexity%2Cncloc
GET https://sonarcloud.io/api/measures/component?component=Vlad8800_QA_1lab%3Aapp%2Fservices.py&metricKeys=complexity%2Ccognitive_complexity%2Cncloc
GET https://sonarcloud.io/api/measures/component?component=Vlad8800_QA_1lab%3Aapp%2Fexport%2Frepository.py&metricKeys=complexity%2Ccognitive_complexity%2Cncloc
GET https://sonarcloud.io/api/measures/component?component=Vlad8800_QA_1lab%3Aapp%2Fconsent%2Fschemas.py&metricKeys=complexity%2Ccognitive_complexity%2Cncloc
GET https://sonarcloud.io/api/measures/component?component=Vlad8800_QA_1lab%3Aapp%2Fservices.py&metricKeys=class_complexity%2Ccoupling_between_objects%2Clcom4
```

## Фрагменти сирих JSON-відповідей

Успішна відповідь сервера для Core Domain (HTTP 200):

```json
{
  "component": {
    "key": "Vlad8800_QA_1lab:app/services.py",
    "path": "app/services.py",
    "language": "py",
    "measures": [
      {"metric": "complexity", "value": "37"},
      {"metric": "cognitive_complexity", "value": "20", "bestValue": false},
      {"metric": "ncloc", "value": "200"}
    ]
  }
}
```

Запит із ключами, дослівно потрібними методичці, повертає HTTP 404:

```json
{
  "errors": [
    {"msg": "The following metric keys are not found: coupling_between_objects"}
  ]
}
```

Це не відсутнє значення в окремому файлі: каталог `/api/metrics/search` містить 165 метрик, але не містить ключів `class_complexity`, `coupling_between_objects`, `cohesion_in_methods`, `lcom4`, `mhf`, `ahf`, `cof`, `dit`. Повний список ключів і URL кожного запиту збережено у сирому JSON. SonarCloud `complexity` — цикломатична складність **файлу**, не класовий WMC.

## Порівняльний паспорт трьох шарів

У стовпцях SonarCloud наведено виключно дані Web API. Локальні оцінки CK наведено окремо; вони не видаються за SonarCloud і не є стандартизованим результатом платформи.

| Шар / файл | Sonar `complexity` файлу | Sonar `cognitive_complexity` | Sonar `ncloc` | Сума WMC класів за Radon | Найбільший CBO proxy одного класу | Найбільший LCOM4 proxy |
|---|---:|---:|---:|---:|---:|---:|
| Core Domain `app/services.py` | 37 | 20 | 200 | 10 | 0 | 3 |
| Infrastructure `app/export/repository.py` | 38 | 23 | 355 | 39 | 0 | 6 |
| Utility/DTO `app/consent/schemas.py` | 0 | 0 | 72 | 0 | 2 | 0 |

За локальним AST/Radon: `ShippingOrderSpec` має WMC 7, LCOM4 proxy 3; `ShippingRateResult` — WMC 3, LCOM4 proxy 3. `UserDataRepository` має WMC 39, LCOM4 proxy 6. DTO-класи у `schemas.py` здебільшого не мають власних методів, тому LCOM4 proxy 0 означає «немає методів», а не ідеальну згуртованість.

Локальні означення: WMC = сума Radon CC методів класу; CBO proxy = число різних класів цього проєкту, явно названих у AST класу; LCOM4 proxy = кількість компонентів зв'язності методів, що спільно використовують поля `self` або викликають один одного. Для LCOM4 ідеал за такою дефініцією — **1**, тож поріг `LCOM < 0,2` з методички належить до іншої, нормалізованої метрики і не може бути застосований до LCOM4. Динамічні виклики Python та неоднозначні імена статичний CBO proxy може пропустити.

## Глобальні коефіцієнти MOOD

SonarCloud не повертає MHF, AHF чи COF через свій каталог метрик. Локальний AST-скрипт дає лише явно визначені **наближення за конвенцією Python**:

| Показник | Локальна оцінка | Як обчислено | Важливе обмеження |
|---|---:|---|---|
| MHF proxy | 0,05 (5%) | 2 методи з початковим `_` / 40 методів без `__dunder__` | `_` — конвенція, не контроль доступу |
| AHF proxy | 1,00 (100%) | 11 полів `self._...` / 11 знайдених полів `self` | AST охоплює лише явно присвоєні поля |
| COF proxy | 0,0248 (2,48%) | 47 спрямованих явних міжкласових посилань / `44 × 43` можливих | Не охоплює динамічні залежності та зовнішні бібліотеки |

Ці коефіцієнти **не є офіційними MOOD**, оскільки точні визначення враховують доступність членів, успадкування та семантику зв'язків, яких статичний огляд Python за домовленостями не доводить. У звіті вони є додатковим орієнтиром, а не підміною вимаганого API-показника.

## Первинний архітектурний вердикт

За доступними даними SonarCloud найбільше уваги серед трьох шарів потребують бізнес-сервіс і репозиторій: їхня складність файлу 37 і 38 відповідно, тоді як DTO-файл має 0. Локальний класовий аналіз вказує на `UserDataRepository` як кандидата для перевірки згуртованості (WMC 39, шість незв'язаних груп методів за AST proxy). Однак доказу критичного God Object або spaghetti-коду **немає**: офіційні CBO/LCOM метрики недоступні, а локальний CBO proxy не виявив великої кількості явних зв'язків у цьому класі. Це базова лінія для подальшого аналізу, не фінальний діагноз.

**Обмеження оцінювання:** формальну вимогу на максимальні 3 бали — отримати саме CK/MOOD числа через REST API SonarQube/SonarCloud — на цьому SonarCloud для Python виконати неможливо, оскільки названі ключі відсутні у каталозі сервера. Для буквального виконання потрібен інший сервер/аналізатор з відповідним плагіном метрик або погоджений із викладачем альтернативний інструмент. Числа не вигадано і не приписано API.
