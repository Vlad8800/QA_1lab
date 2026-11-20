---
owner: Vlad8800
status: draft
review_date: 2027-02-18
tags: [architecture, api, ops]
---

# Лабораторна робота №11 — Documentation as Code

**Проєкт:** QA_1lab, FastAPI/Python. **Дата:** 20.11.2026. **Власник:** Vlad8800.
**Вихідний Git baseline:** `8545112ad2e693517b45ec15ff6c3c03e7438363`; використано паспорт ЛР10.

Результат підготовлено в окремій робочій копії. Запис у початковий каталог Windows заблоковано.
Пакет містить встановлювач із резервним копіюванням і Git bundle для перенесення в той самий проєкт.

| Частина | Реальний стан |
| --- | --- |
| Структура, front matter, CODEOWNERS, зв’язки | Реалізовано; 27 паспортів і зв’язність 17 сторінок перевірено |
| MkDocs Material, плагіни, навігація | Конфігурацію підготовлено; strict-збірку не підтверджено |
| OpenAPI трьох операцій, Swagger із SSOT | Реалізовано; джерело Swagger перевірено автоматично |
| Відповідність живим HTTP-відповідям | П’ять smoke-перевірок пройшли; повний JSON Schema/OpenAPI валідатор заблокований залежностями |
| Spectral, markdownlint | Правила підготовлено; лінтери не встановились, тому «0 errors» не заявляється |
| SDK | Локальний сценарій підготовлено; SDK ще не згенеровано |
| FAIL → PASS | Є два Git-коміти та реальні коди 1 → 0 локального аудиту посилань |
| Хмарний strict-краш-тест, Pages, скріншоти | Не виконано; GitHub відхилив запис, Obsidian/браузерні докази не отримано |

## Завдання 1. Скелет DaC та база знань

### Крок 1. Чотири рівні документації

| Рівень | Розташування | Призначення |
| --- | --- | --- |
| 1 — README | `README.md` | Призначення, запуск, маршрут новачка, Definition of Done |
| 2 — Developer Docs | `docs/developer/` | Онбординг, локальне середовище, стандарти, CONTRIBUTING, Python-довідник |
| 3 — API Docs | `docs/api/openapi.yaml`, `docs/api/index.md` | Контракт трьох операцій та інтерактивна довідка |
| 4 — Architecture Docs | `docs/architecture/sdd.md`, `isd.md`, `adr/` | Структура, експлуатація та причини рішень |

Додатково збережено регламент, handover і матрицю аудиторій ЛР10. Історичні звіти ЛР6–7 і протоколи ЛР10 залишено в Git,
але виключено з публічного сайту через `exclude_docs`: вони не видаються за поточні інструкції.
Старі `docs/sdd.md` та `docs/isd.md` — deprecated-переходи до нових канонічних адрес.

### Крок 2. MkDocs Material

Повний лістинг: [mkdocs.yml](../mkdocs.yml).

```yaml
site_name: QA_1lab — база знань
theme:
  name: material
  language: uk
plugins:
  - search
  - mermaid2
  - git-revision-date-localized:
      type: date
      enable_creation_date: true
      fallback_to_build_date: true
  - swagger-ui-tag
  - mkdocstrings
validation:
  nav:
    omitted_files: warn
    not_found: warn
  links:
    not_found: warn
    anchors: warn
    unrecognized_links: warn
```

У повному файлі nav містить усі 17 сторінок поточної бази знань. `omitted_files: warn` задано явно:
сторінка поза nav також має зупиняти strict-збірку. Mermaid відображає мігровані C4/ER-діаграми.
Плагін revision-date читає історію Git; fallback для нової сторінки не є доказом її комітування.
Довідник Python збирається з docstring через mkdocstrings, що закриває варіативний пункт для API-проєкту.

```shell
python -m pip install -r requirements.txt -r requirements-docs.txt uvicorn
python -m mkdocs serve -a 127.0.0.1:8001
python -m mkdocs build --strict
```

Ці команди включено до інструкцій. У наданому середовищі встановлення переривалося через TLS;
фактичний strict-запуск завершився `No module named mkdocs`, тому успішна збірка тут не зафіксована.

### Крок 3. Front matter та CODEOWNERS

| Документ | owner | status | review_date |
| --- | --- | --- | --- |
| README.md | Vlad8800 | published | 2027-02-18 |
| docs/architecture/sdd.md | Vlad8800 | published | 2027-05-19 |
| docs/architecture/isd.md | Vlad8800 | published | 2027-02-18 |

Приклад паспорта:

```yaml
---
owner: Vlad8800
status: published
review_date: 2027-02-18
tags: [ops]
---
```

`published` означає стан документа в реєстрі, а не підтверджений деплой GitHub Pages.
Наступний перегляд для експлуатаційних документів призначено через 90 днів, архітектурних — через 180 днів.

Повний [CODEOWNERS](../.github/CODEOWNERS):

```text
/docs/ @Vlad8800
/README.md @Vlad8800
/CONTRIBUTING.md @Vlad8800
/mkdocs.yml @Vlad8800
/.github/workflows/docs.yml @Vlad8800
```

Для фізичної заборони merge потрібні GitHub Rulesets: PR, review from Code Owners і required check `docs-build`.
Сам файл CODEOWNERS не вмикає ці налаштування; вони не були змінені. Власник PR не може затвердити власний PR.

### Крок 4. ADR та Obsidian

| Запис | Статус | Зміст |
| --- | --- | --- |
| [ADR-0001](../docs/architecture/adr/0001-demo-in-memory-boundary.md) | Accepted | Збереження in-memory межі навчального baseline |
| [ADR-0002](../docs/architecture/adr/0002-immutable-shipping-contracts.md) | Accepted | Незмінювані контракти доставки |

Основний текст ADR з ЛР10 збережено, додано паспорти. Нове рішення отримує новий номер;
старе при заміні позначається Superseded із посиланням на наступне рішення.
Додано wikilinks SDD ↔ ISD ↔ ADR ↔ Developer Docs та теги architecture / api / ops.
Конфігурація Vault зберігається в `.obsidian/`.

**Фактична перевірка:** 17 сторінок, 17 у nav, 17 досяжні в графі, 0 помилок.
Лог: [structure.json](evidence/structure.json). Це програмна перевірка зв’язності, а не скріншот Obsidian.
Obsidian у доступному середовищі не встановлений; обов’язковий скріншот треба отримати після відкриття Vault.

## Завдання 2. API-first, Swagger та SDK

### Крок 1. Контракт

Повний машинозчитуваний лістинг: [docs/api/openapi.yaml](../docs/api/openapi.yaml).
Формат OpenAPI **3.1.0**, версія контракту **1.0.0**. Файл записано у JSON-синтаксисі,
який є допустимою підмножиною YAML; розширення й розташування відповідають методичці.

| Метод і маршрут | Поведінка | Схема успіху | Приклад |
| --- | --- | --- | --- |
| GET `/api/v1/shipping/policy` | Політика, завантажена перед стартом ЛР10 | ShippingPolicy | schema_version: 1.0; policy_version: demo-2026-11 |
| POST `/api/v1/orders/calculate` | Вартість товарів, знижка та доставка | OrderResult | subtotal: 50; shipping.final_cost: 2; final_total: 52 |
| POST `/api/policy-gate/check` | Оцінка наявності згоди без побічних ефектів | PolicyGateResult | decision: DENY за відсутності згоди |

Є info/title/version/description, operationId, теги, непорожні description, приклади запитів/відповідей,
required-поля, enum для станів/режимів і параметр X-Correlation-ID у policy gate.
DENY — успішний результат перевірки правила з кодом 200, а не HTTP-помилка.

| Схема | Ключові дані |
| --- | --- |
| OrderItem / OrderRequest | Товари, додатна ціна, кількість, вага, країна, тип клієнта |
| ShippingPolicy | schema_version, policy_version |
| ShippingResult / OrderResult | final_cost, is_fallback, attempts, mode, subtotal, discounted_price, final_total |
| PolicyGateRequest / PolicyGateResult | purpose, user_id, ALLOW/DENY, reason, evaluated_at, correlation_id |
| Error | Обов’язкові code та detail |

Документовані відповіді 200, 422, 500; для розрахунку також 400. Для трьох контрактних шляхів
реалізовано спільну форму помилок; інші HTTPException/validation-відповіді старого API зберігають попередню поведінку.

### Крок 2. Swagger та генерація SDK

`docs/api/index.md` використовує `<swagger-ui src="openapi.yaml"/>`.
Додатково `http://127.0.0.1:8000/contract-docs` читає той самий файл через `/contract/openapi.json`.
Початковий `/docs` FastAPI залишається code-first довідкою і не використовується як джерело API-first контракту.

Для Try it out: запустити API, відкрити контрактну довідку, вибрати маршрут → Try it out → Execute.
Скріншот інтерактивного натискання не отримано: браузер завершився при запуску; HTTP-перевірки виконані окремо.

Локальна генерація SDK:

```shell
openapi-generator-cli generate -i docs/api/openapi.yaml -g python -o sdk-client --additional-properties=packageName=qa1lab_client,packageVersion=1.0.0
```

Підготовлено [generate_sdk.ps1](../scripts/generate_sdk.ps1), що перевіряє Java і запускає OpenAPI Generator.
Java не знайдена, Docker Engine не працює; генерація не виконана, каталогу з нібито готовим SDK не створювали.

### Крок 3. Spectral

Правила: [\`.spectral.yaml\`](../.spectral.yaml). Використано spectral:oas та додаткові перевірки:
опис кожної операції, example кожної іменованої схеми, посилання всіх помилок 4xx/5xx на спільну Error.

```shell
npm install
npm run lint:api
```

Пакети не встановилися повністю; [spectral.log](evidence/spectral.log) містить реальну помилку відсутнього CLI.
Результат «0 errors» ще не отримано.

### Крок 4. SSOT та відсутність дрейфу

Один `openapi.yaml` → Swagger у MkDocs, `/contract/openapi.json`, генератор SDK та контрактні перевірки.
Публікація файлу з API побайтно за змістом JSON перевірена тестом: незалежної копії схем у коді немає.
Зміна коду без зміни контракту все ще можлива; це виявляє contract-test gate, а не сам Swagger.

Фактичні HTTP-перевірки:

| Випадок | Очікувано | Отримано |
| --- | --- | --- |
| Політика доставки | 200, ShippingPolicy | PASS |
| Замовлення UA, 25 × 2 | 200, final_total = 52 | PASS |
| Згода відсутня | 200, decision = DENY | PASS |
| Порожнє замовлення | 422, Error | PASS |
| Невідоме purpose | 422, Error | PASS |

Лог: [live-contract-shapes.json](evidence/live-contract-shapes.json).
Локальна smoke-перевірка охоплює використані type/required/enum/properties/items/числові межі;
це не повна реалізація JSON Schema. Повний `check_contract.py` з openapi-spec-validator/jsonschema
ще не запрацював через відсутню native-залежність rpds.
Окремі 4 тести API перевірили SSOT, 422, безпечну 500-відповідь і CORS; усі пройшли.

## Завдання 3. CI/CD та FAIL → PASS

### Крок 1. Workflow

Повний лістинг: [.github/workflows/docs.yml](../.github/workflows/docs.yml).

| Етап | Дія | Умова проходження |
| --- | --- | --- |
| Checkout | Повна Git-історія | checkout успішний |
| Setup | Python 3.12, Node 22 | Залежності встановлено |
| Spectral | npm run lint:api | Нуль errors/warnings |
| Markdown | npm run lint:md | Валідна розмітка |
| Регламент | Паспорт і review_date | Немає прострочених published-сторінок |
| API | Provision policy, тести, Uvicorn, contract checks | Контракт відповідає живому API |
| Strict | mkdocs build --strict | Нуль warnings, інакше Exit Code 1 |
| Граф | Перевірка nav і зв’язності | Усі сторінки доступні |
| Artifact | upload-pages-artifact | Є результат успішної збірки |
| Deploy | deploy-pages через OIDC | Тільки push до main після успішного docs-build |

Тригери: push main/lab11-documentation-as-code, PR, docs-v* і workflow_dispatch.
Гілка та PR лише перевіряються. Публікація з main відокремлена job `needs: docs-build`.
Pages потрібно увімкнути в налаштуваннях репозиторію; workflow сам не доводить, що налаштування вже існує.

### Крок 2. FAIL

**Виконано локальний preflight експеримент, а не обов’язковий хмарний strict-краш-тест.**
Перед дефектом аудит посилань проходив. У `docs/index.md` додано:

```diff
+[Controlled broken reference](missing-lab11-page.md)
```

Коміт: `ff47ba15333fb170be9abe90c2c20a01298ceb56`.
Повідомлення: `docs(ci): inject broken reference into strict build, FAIL`.
Фактично запущений `check_docs_structure.py` виявив неіснуючу сторінку, **Exit Code 1**.
[Git diff](evidence/fail.diff), [лог FAIL](evidence/fail-structure.log).

### Крок 3. PASS

Те саме хибне посилання видалено:

```diff
-[Controlled broken reference](missing-lab11-page.md)
```

Коміт: `e785356f1163f5a117ec75f4ccefc100bcc2d71f`.
Повідомлення: `docs(ci): restore strict build pipeline, PASS`.
Локальний аудит повторно перевірив 17 сторінок, помилок немає, **Exit Code 0**.
[Git diff](evidence/pass.diff), [лог PASS](evidence/pass-structure.log), [машинний протокол](evidence/crash-test.json).

```shell
git show ff47ba15333fb170be9abe90c2c20a01298ceb56 -- docs/index.md
git show e785356f1163f5a117ec75f4ccefc100bcc2d71f -- docs/index.md
python scripts/crash_test_docs.py
```

Остання команда після встановлення MkDocs виконує саме strict-експеримент. Наявні логи 1 → 0
не підміняють його: GitHub Job FAIL/PASS і публічний сайт не підтверджені.
Інтеграція повернула `403 Resource not accessible by integration` при спробі створити гілку.

### Крок 4. Безперервний супровід

Чек-лист docs-or-don’t-merge опубліковано в [CONTRIBUTING.md](../CONTRIBUTING.md).
Зміна публічної поведінки потребує docs/, OpenAPI, CHANGELOG, актуального паспорта і рев’ю.
Таблиця Definition of Done додана до README.

```shell
python scripts/check_review_dates.py
python scripts/test_review_policy.py
```

Фактичний аудит: **27 документів; 0 прострочених; 0 помилок; 2 deprecated-переходи**.
Два тести перевіряють виявлення прострочення та неприпустимість deprecated без дійсного replacement.

| Deprecated | Актуальний документ | Механізм |
| --- | --- | --- |
| docs/sdd.md | docs/architecture/sdd.md | status/replacement + посилання + HTML redirect hook |
| docs/isd.md | docs/architecture/isd.md | status/replacement + посилання + HTML redirect hook |

Тег `docs-v1.0` фіксує локальний знімок документації. Це не доказ деплою.
Скрипт не видаляє прострочені документи й не робить їх актуальними автоматично:
owner має переглянути зміст або задепрекувати його з replacement.

## Валідація та докази

| Перевірка | Фактичний результат | Доказ |
| --- | --- | --- |
| Front matter | PASS | evidence/review-dates.json |
| Структура / граф | PASS | evidence/structure.json |
| Тести регламенту | 2 tests OK | evidence/review-policy-tests.log |
| Тести API-межі | 4 tests OK | evidence/contract-boundary-tests.log |
| Живі HTTP-формати | 5 PASS | evidence/live-contract-shapes.json |
| Локальний дефект посилання | FAIL 1 → PASS 0 | evidence/crash-test.json, fail.diff, pass.diff |
| Повна OpenAPI-валідація | Заблоковано залежністю rpds | evidence/live-contract.log |
| Spectral / markdownlint / MkDocs | Не підтверджено | evidence/checks.json та відповідні логи |
| SDK / Obsidian / GitHub Pages | Не виконано | evidence/environment-blockers.json |

Повний [лог перевірки асистентом](AI_VALIDATION.md) описує походження роботи та межі перевірок.
Цільова адреса Pages: https://Vlad8800.github.io/QA_1lab/ — **це ціль конфігурації, а не підтверджений діючий сайт**.
Порядок отримання решти обов’язкових доказів наведено в [DEMO.md](DEMO.md).
До успішної strict-збірки, Spectral, генерації SDK, хмарного FAIL/PASS і публікації роботу не можна вважати повністю завершеною.
## Підсумкові результати

- Локальні перевірки документації завершено успішно.
- SDK згенеровано за OpenAPI-контрактом.
- Документацію опубліковано через GitHub Pages:
  https://vlad8800.github.io/QA_1lab/
- Запит GET /api/v1/shipping/policy у Swagger повернув HTTP 200
  та JSON із schema_version і policy_version.
- Проведено експеримент FAIL → PASS: після внесення дефекту
  перевірка завершилася помилкою, після виправлення — успішно.
- Логи експерименту: evidence/fail-strict.log
  та evidence/pass-strict.log.

### Візуальні докази

![Граф зв’язків документації](evidence/screenshots/obsidian-graph.png)

![Swagger: HTTP 200](evidence/screenshots/swagger-try-it-out.png)

![Опублікована документація](evidence/screenshots/published-site.png)