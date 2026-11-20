---
owner: Vlad8800
status: published
review_date: 2027-02-18
tags: [ops]
---

# Handover Package

Дата: 2026-11-15. Передавач і поточний owner: Vlad8800. Команда супроводу та дублер поки не призначені. [Регламент з датами](maintenance.md), [звіт експерименту](lab10/task3-report.md), [SDD](sdd.md), [ISD](isd.md).

## Реєстр передачі

| Документ | Owner | Статус на передачу |
| --- | --- | --- |
| README.md | Vlad8800 | Оновлено після FAIL, містить provision JSON і нову поведінку |
| docs/sdd.md | Vlad8800 | Оновлено: policy loader, C4 file storage, новий HTTP-контракт |
| docs/isd.md | Vlad8800 | Оновлено: порядок запуску й чинний env override |
| ADR-0001/0002 та індекс | Vlad8800 | Застосовність переглянута; первинні рішення збережені |
| docs/audience-matrix.md | Vlad8800 | Питання чотирьох аудиторій документально покриті |
| docs/maintenance.md | Vlad8800 | Owner, цикл, last_review, review_date та merge-правило задані |

## Онбординг нового розробника — 5 кроків

1. Прочитати [README](index.md): призначення, demo principal, in-memory обмеження. Отримати гілку PASS з Git bundle за DELIVERY.md.
2. За [SDD](sdd.md#component-map) знайти власний компонент, його викликачів, моделі й HTTP/internal contracts; прочитати два [ADR](architecture/adr/README.md).
3. Створити Python 3.11 venv і встановити залежності за README. За [ISD](isd.md#shipping-policy) підготувати runtime/shipping-policy.json **перед** запуском одного API worker.
4. Перевірити GET /api/v1/shipping/policy, UA-розрахунок final_total=52, виконати pytest. Результат і версії середовища записати: старі тайм-аути з task2 не видавати за PASS нового HTTP-запуску.
5. Виконати read-only аудит scripts/audit_documentation_currency.py; пройти з owner сценарії export/consent/erasure і recovery. Новий учасник самостійно пояснює компонент; тільки після цього фіксується дублер і повторюється Bus Factor review.

## Bus Factor declaration

Git підтверджує одного автора/maintainer Vlad8800. Це не психологічний доказ, що ніхто інший не розуміє код. Немає зафіксованого незалежного дублера чи передачі знань; тому консервативна оцінка **підтвердженого Bus Factor = 1**, ціль >=2.

| Компонент / темна зона | Підтверджений owner / дублер | Ризик втрати знань | План і критерій закриття |
| --- | --- | --- | --- |
| Orders, frozen DTO, тарифні таблиці | Vlad8800 / немає | Високий: зміна сум/контракту | Призначити другого розробника; він пояснює ADR-0002 і самостійно змінює тестовий тариф з regression tests |
| Export/erasure та in-memory зв’язки | Vlad8800 / немає | Високий: втрати state/хибна транзакційна гарантія | Парне рев’ю SDD та ADR-0001; дублер повторює export→erasure→verify і пояснює restart-loss |
| Consent gate і purpose/version | Vlad8800 / немає | Високий: неправильно дозволена модельована дія | QA + розробник повторюють grant/allow/revoke/deny й cross-purpose denial |
| Privacy sanitization, regex/log fields | Vlad8800 / немає | Високий: витік/складні edge cases | Документувати allow/redact boundaries; другий QA відтворює негативні тести без raw PII у логах |
| CI, Git hooks, quality gates | Vlad8800 / немає | Середній/високий: плутанина локального hook та CI gate | DevOps-дублер запускає scanner і пояснює Sonar/Hotspots trigger та provisioning policy |
| Новий policy loader і startup path | Vlad8800 / немає | Середній: API не підніметься за старим README | Новачок піднімає чистий checkout з missing→provision→load, фіксує GET та tests |

Ролі другого розробника/QA/DevOps — **план**, не вигадані учасники чи проведені зустрічі. Ціль: призначення дублерів до 2026-11-22; незалежний onboarding/restore drill до 2026-11-29. Історичні матеріали ЛР6/7 мають цінність як докази; дублікати без нового споживача не повинні заміняти канонічні документи.

## Always Ready to Handover verdict

**NO — повна організаційна готовність ще не доведена.** Паспорт актуалізований, пакет і відтворюваний FAIL/PASS є, але підтверджений Bus Factor лишається 1, незалежний онбординг не проведений, повний HTTP/production restore не підтверджений. Це не FAIL документаційного експерименту: відповідність code/docs відновлена, але документ не може вигадати другого носія знань.

Умови переходу в YES: дублер >=1 для критичних зон; незалежно виконаний onboarding і тестовий запуск; задокументований restore drill у цільовому середовищі; доступні owner/review dates і пройдений документаційний контроль при кожній зміні. До цього статус — готовий пакет для контрольованої передачі з відкритими ризиками.
