---
owner: Vlad8800
status: published
review_date: 2027-05-19
tags: [architecture]
---

# ЛР10 — Завдання 3: Documentation Maintenance, FAIL → PASS

Дата: 15.11.2026. Репозиторій QA_1lab; початковий паспорт a844497. Експеримент виконується в окремій локальній гілці lab10-documentation-maintenance, без push/merge до main.

## 1. Регламент

[maintenance.md](../maintenance.md) призначає owner Vlad8800, 90 днів для README/ISD та 180 для SDD/ADR, last_review=2026-11-15. Наступні дати: 2027-02-13 та 2027-05-14. Позачергове рев’ю обов’язкове після зміни. Правило «зміна коду = зміна документації» — процесна умова merge; GitHub branch protection не заявляється налаштованим.

## 2. FAIL-протокол

Baseline після регламенту: `4f20c7e607cc68849c06be2196746e4d66fb7958`. FAIL: `b2649382206b22b69fe6b38acfdced3ea930cb28`, повідомлення **docs(audit): simulate documentation decay, FAIL**.

Контрольована зміна: новий `app/shipping_policy.py`, descriptor-template в config/, обов’язковий startup-load перед FastAPI import і новий GET /api/v1/shipping/policy. runtime/ ігнорується Git; файл треба provision перед API. Зміна не додає платного сервісу й не змінює тарифні суми. У FAIL немає жодної зміни Markdown: це перевіряється diff назвами та blob SHA документів. Повний фактичний Git-diff включений до evidence/fail.diff у пакеті.

```diff
+from app.shipping_policy import load_shipping_policy
+shipping_policy = load_shipping_policy()
+@app.get('/api/v1/shipping/policy')
+def get_shipping_policy():
+    return dict(shipping_policy)
```

| Аудиторія | Що обіцяє старий паспорт | Фактична зміна і шкода |
|---|---|---|
| Новачок | Встановити deps і запустити Uvicorn | Пропущений JSON provision: startup завершується RuntimeError |
| Бізнес | Перелік поведінки системи в README | Нова видимість версії policy відсутня; старе твердження про достатність кроків запуску хибне. Старі суми не називаються зміненими |
| Розробники | Карта компонентів не має loader/config store | Нова файловa залежність до API startup невідома, structure drift |
| QA | Таблиця контрактів не має GET policy | Немає очікуваного response/error startup contract |
| DevOps | Checkout/deps → API, без provision | Тепер потрібен JSON → API; старий порядок deployment непрацездатний |

Read-only експериментальний auditor повернув FAIL за всіма чотирма checks: README behavior, README startup, SDD component/contract, ISD provision. Без документації новачок знав би про прогалину; стара впевнена інструкція натомість приводить до відмови — конкретний прояв ілюзії розуміння. Це демонстрація, не вимірювання порівняльної шкоди на людях.

## 3. Метрики до/після

Nc — коміти, що зачіпають app; Nd — коміти конкретного документа; Ratio=Nc/Nd. Gap — коміти app після останнього doc update. Дата аудиту фіксована, 2026-11-15.

| Стан | README, SDD, ISD: Age | Nc | Nd кожного | Ratio кожного | Gap |
|---|---|---|---|---|---|
| Baseline | 0 днів | 23 | 1 | 23.00 | 0 |
| FAIL | 0 днів | 24 | 1 | 24.00 | 1 |
| PASS після документального коміту | 0 днів | 24 | 2 | 12.00 | 0 |

**Age не деградує за один день.** Дати не зміщувалися штучно. Кількісний доказ — Ratio 23→24 і Gap 0→1 при незмінених doc blobs, а після відновлення Gap=0. Пороги 90/180 днів та >20 послідовних змін без документації не перевищені; малий дрейф уже небезпечний, а не стає безпечним через відсутність порогового сигналу. Ratio>20 саме по собі не означає 20 незадокументованих змін.

```powershell
git diff b264938^ b264938 -- README.md docs/sdd.md docs/isd.md
git diff b264938^ b264938 -- app/main.py app/shipping_policy.py config/shipping-policy.example.json
git log -1 --format=%cs b264938 -- README.md
@(git log --format=%H b264938 -- app).Count
@(git log --format=%H b264938 -- README.md).Count
python scripts/audit_documentation_currency.py --ref 4f20c7e
python scripts/audit_documentation_currency.py --ref b264938
python scripts/audit_documentation_currency.py --ref HEAD
```

Auditor має вузьку явну область: шукає відомий новий компонент/endpoint/provision у паспорті; він не доводить семантичну повноту довільної документації. Сирі JSON baseline/fail/pass і Git-команди знаходяться в evidence/ пакета. PASS SHA записаний у зовнішньому DELIVERY.md, щоб уникнути циклу «коміт містить власний SHA».

## 4. PASS-протокол

Коміт **docs(maintenance): restore documentation currency, PASS** оновлює README (новий GET і підготовка файла), SDD (C4 file store, loader, контракт), ISD (SHIPPING_POLICY_FILE і provision-before-API), регламент (позачерговий перегляд того ж дня), матрицю аудиторій. Sonar workflow також provision-ить template перед pytest, щоб нова startup-залежність не ламала наявний CI test step. ADR-0001/0002 не переписані.

Після відновлення endpoint залишається в коді — PASS не є rollback нової функції. Відновлюється правдивість інструкцій. README має `Copy-Item config/shipping-policy.example.json runtime/shipping-policy.json`; ISD пояснює default/env path; SDD описує schema_version/policy_version. Чотири області аудиту мають PASS, матриця аудиторій знову документально покрита.

## 5. Handover та межі перевірки

[handover.md](../handover.md) містить власників, статуси, 5-кроковий onboarding, шість зон Bus Factor, цілі дублювання знань і вердикт. Підтверджений Bus Factor консервативно оцінений як 1 за наявними записами; відсутність дублера не замінено вигаданим «парним рев’ю».

Межі runtime: у task2 повний HTTP-прогін мав тайм-аути; цей протокол не видає їх за PASS. У task3 новий loader перевіряється незалежно від FastAPI і localhost; selected pytest перевіряє loader та services. Git/AST/документаційні checks перевіряють дрейф і виправлення; вони не є production restore drill.

Фінальний вердикт **Always Ready to Handover = NO до незалежного onboarding/дублера**. Документаційний FAIL→PASS завершений, але організаційний single point of knowledge лишається чесно відкритим ризиком.
