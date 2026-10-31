# Project Hub — Лабораторна робота №8

**Дисципліна:** Інженерія якості та супровід програмних систем  
**Тема:** аудит об’єктного дизайну, декомпозиція God Object, заміна успадкування композицією  
**Репозиторій:** [Vlad8800/QA_1lab](https://github.com/Vlad8800/QA_1lab/tree/lab8-architecture), гілка `lab8-architecture`  
**Стан:** код, експерименти Baseline → FAIL → PASS, тести та звіти підготовлені до демонстрації. Обмеження платформи SonarCloud наведено нижче.

## Матеріали та докази

- [Повний звіт завдання 1 — ООП-паспорт](https://github.com/Vlad8800/QA_1lab/blob/lab8-architecture/docs/lab8/%D0%97%D0%B0%D0%B2%D0%B4%D0%B0%D0%BD%D0%BD%D1%8F%201%20%D0%9E%D0%9E%D0%9F%20%D0%BF%D0%B0%D1%81%D0%BF%D0%BE%D1%80%D1%82%20SonarCloud.md), [сирі відповіді SonarCloud](https://github.com/Vlad8800/QA_1lab/blob/lab8-architecture/docs/lab8/task1-artifacts/sonar_api_baseline.json).
- [Повний звіт завдання 2 — God Object](https://github.com/Vlad8800/QA_1lab/blob/lab8-architecture/docs/lab8/%D0%97%D0%B0%D0%B2%D0%B4%D0%B0%D0%BD%D0%BD%D1%8F%202%20God%20Object.md), [матриця і граф Baseline](https://github.com/Vlad8800/QA_1lab/tree/lab8-architecture/docs/lab8/task2-artifacts/baseline), [FAIL-лог](https://github.com/Vlad8800/QA_1lab/blob/lab8-architecture/docs/lab8/task2-artifacts/fail/pytest.log), [PASS-метрики](https://github.com/Vlad8800/QA_1lab/blob/lab8-architecture/docs/lab8/task2-artifacts/pass/oo_metrics.json).
- [Повний звіт завдання 3 — успадкування і композиція](https://github.com/Vlad8800/QA_1lab/blob/lab8-architecture/docs/lab8/%D0%97%D0%B0%D0%B2%D0%B4%D0%B0%D0%BD%D0%BD%D1%8F%203%20%D0%A3%D1%81%D0%BF%D0%B0%D0%B4%D0%BA%D1%83%D0%B2%D0%B0%D0%BD%D0%BD%D1%8F%20%D1%96%20%D0%BA%D0%BE%D0%BC%D0%BF%D0%BE%D0%B7%D0%B8%D1%86%D1%96%D1%8F.md), [незалежна перевірка DIT через Python MRO](https://github.com/Vlad8800/QA_1lab/blob/lab8-architecture/docs/lab8/task3-artifacts/runtime_dit_validation.json), [справжній скріншот історії Git](https://github.com/Vlad8800/QA_1lab/blob/lab8-architecture/docs/lab8/task3-artifacts/git_history_terminal.png).
- [Успішна хмарна збірка PASS для завдання 3](https://github.com/Vlad8800/QA_1lab/actions/runs/41221150865).

## Завдання 1. Програмний ООП-паспорт

Сканування SonarCloud у GitHub Actions та прямі запити до `/api/measures/component` дали відтворюваний зріз трьох архітектурних ролей. У таблиці наведено **файлові** метрики, які дійсно повернув Web API:

| Роль і файл | Complexity | Cognitive complexity | NCLOC |
|---|---:|---:|---:|
| Core Domain — `app/services.py` | 37 | 20 | 200 |
| Infrastructure — `app/export/repository.py` | 38 | 23 | 355 |
| Utility/DTO — `app/consent/schemas.py` | 0 | 0 | 72 |

Окремий локальний AST/Radon-аналіз побудував оцінки класових показників і наближення MOOD: **MHF 5%, AHF 100%, COF 2,48%**. Це показники за явно описаними правилами для Python, **не офіційні метрики SonarCloud**. Найбільше уваги за доступними даними потребують бізнес-сервіс і репозиторій; самі лише файлові числа не доводять наявності God Object.

## Завдання 2. Локалізація та усунення God Object

Оскільки природного класу з критичним зачепленням не було виявлено, використано дозволену методичкою контрольну агрегацію. У [Baseline-коміті `59b6318`](https://github.com/Vlad8800/QA_1lab/commit/59b6318) `PrivacyOperationsGodObject` поєднав чотири обов’язки: згоди, маркетингову відправку, експорт та видалення даних. Локальні показники: **CBO proxy 16**, **LCOM4 proxy 6**, нормалізована оцінка незв’язності **0,625**.

У [FAIL-коміті `76b4f0a`](https://github.com/Vlad8800/QA_1lab/commit/76b4f0a) змінено назву одного параметра залежного сервісу. Моноліт продовжив передавати старий іменований аргумент, тому виник `TypeError`: **4 failed, 5 passed**. Це зафіксований приклад Shotgun Surgery.

У [PASS-коміті `0190df8`](https://github.com/Vlad8800/QA_1lab/commit/0190df8) моноліт замінено чотирма класами `ConsentWorkflow`, `MarketingWorkflow`, `ExportWorkflow`, `ErasureWorkflow`. Вони отримують залежності через конструктор і вузькі `Protocol`-контракти. [Наступний коміт `9c401a9`](https://github.com/Vlad8800/QA_1lab/commit/9c401a9) переніс також реальні рішення зі старого сервісу до окремих компонентів. Максимальний CBO proxy чотирьох нових workflow знизився **з 16 до 4**, а серед оновлених класів підсистеми становить **7 ≤ 8**; нормалізована оцінка незв’язності нових workflow — **0 ≤ 0,2**. Після рефакторингу: **52 passed**, хмарне сканування пройшло успішно. Усі ці CBO/LCOM числа — локальні оцінки, а не відповідь SonarCloud API.

## Завдання 3. Вертикальний аудит і композиція

У [Baseline-коміті `0110a85`](https://github.com/Vlad8800/QA_1lab/commit/0110a85) створено контрольну трирівневу ієрархію правил доставки. Найглибший клас мав **DIT 3**, **PIM 4** та **2 перевизначені методи**. PIM не досяг орієнтира понад 20; його не збільшували штучними методами.

У [FAIL-коміті `ff1ba30`](https://github.com/Vlad8800/QA_1lab/commit/ff1ba30) базовому методу додано обов’язковий аргумент `policy_context`. Виклики `super()` у нащадках не передали його: **3 failed, 53 passed**. У [PASS-коміті `91beb7c`](https://github.com/Vlad8800/QA_1lab/commit/91beb7c) успадкування замінено композицією з передачею залежностей через конструктор. Максимальний **DIT знизився з 3 до 1**, перевизначених методів стало **0**, повний набір тестів — **57 passed**. Значення незалежно підтвердили аналіз AST і фактичний Python MRO. [Скріншот термінала](https://github.com/Vlad8800/QA_1lab/blob/lab8-architecture/docs/lab8/task3-artifacts/git_history_terminal.png) показує три послідовні Git-стани.

## Важлива межа вимірювання

Підключений SonarCloud не має у каталозі ключів `class_complexity`, `coupling_between_objects`, `lcom4`, `mhf`, `ahf`, `cof` і `dit`. Запит CK-ключів повертає HTTP 404, а запит DIT — порожній `measures`. Тому **буквально підтвердити CK/MOOD/DIT через цей Web API неможливо**. Звіти зберігають сирі відповіді сервера й окремо позначають локальні розрахунки. Максимальний бал залежить від того, чи викладач прийме цей інструментальний еквівалент. У звітах також відкрито зазначено використання Codex для коду, аналізу та рефакторингу.

## Коротка перевірка на захисті

У локальній папці `C:\Users\Vlad\Documents\Навчання\Тестування\8`:

```powershell
git log --graph --oneline --decorate 0110a85^..91beb7c
Get-Content docs\lab8\task2-artifacts\fail\pytest.log
Get-Content docs\lab8\task3-artifacts\fail\pytest.log
Get-Content docs\lab8\task3-artifacts\runtime_dit_validation.json
docker run --rm -v "${PWD}:/workspace" -w /workspace --entrypoint python lab8-test-env:latest -m pytest -q --tb=short -p no:warnings
```

Остання команда використовує **локально створений** образ `lab8-test-env:latest`. Перед показом студенту слід пояснити відмінність файлової `complexity` від WMC класу, причину обох FAIL-станів, роль контрактів `Protocol` та принцип композиції.
