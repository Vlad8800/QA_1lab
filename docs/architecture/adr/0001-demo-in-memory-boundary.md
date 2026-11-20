---
owner: Vlad8800
status: published
review_date: 2027-05-19
tags: [architecture]
---

# ADR-0001 — Зберегти in-memory storage у межах навчального baseline

## Number and status

Номер: **0001**. Дата рішення про поточну межу: **15.11.2026**. Статус: **Accepted — лише навчальний baseline**. Відповідальний: maintainer `Vlad8800`. Supersedes: немає. Superseded by: немає.

## Context

У коді `8545112` є один FastAPI application і спільний `UserDataRepository` з Python dict/list. Експорт, анонімізація та керування згодами використовують той самий singleton. Вправи й тести потребують відтворюваного seed, простого запуску та перевірки послідовності дій. Підключення зовнішньої БД зараз не є частиною реалізованого середовища.

Цей ADR **не приписує заднім числом** причини автору початкової реалізації (`de038d9`, 16.10.2026). Він сьогодні фіксує рішення зберегти наявну реалізацію для лабораторного baseline й явно обмежити її застосування. Старий `.env.example` зі SQLite не є доказом розгорнутої БД.

## Alternatives

| Альтернатива | Переваги | Вартість / межі |
| --- | --- | --- |
| In-memory dict/list в одному процесі | Немає DB setup; явні fixtures; простий reset і тести | Втрата змін після restart; немає транзакцій, міжпроцесної узгодженості та backups |
| SQLite file | Локальна персистентність, транзакції, невеликий deployment | Потрібні схема, міграції та адаптер; файл/backup/concurrency стають окремою відповідальністю |
| PostgreSQL | Транзакції, constraints, спільний стан для workers | Окремий сервіс, credentials, міграції, backup/restore та супровід |

## Decision

Для навчального baseline залишити один runtime-процес і спільний in-memory repository. У quick start використовувати один worker, описати скидання стану після перезапуску. Не називати пам’ять SQLite/production DB та не обіцяти RPO для runtime mutations.

Для реального production storage рішення відкрите: потрібен новий ADR із вимогами persistence/transactions/access control/restore. Цей документ не реалізує міграцію і не схвалює обробку реальних даних у поточному demo-сховищі.

## Consequences

Позитивні: новачок запускає приклад без БД; тестам легко ізолювати стан; усі модулі мають спільне джерело даних у межах одного процесу.

Компроміси: кожний worker матиме незалежну копію; restart втрачає grant/revoke/erasure і відтворює seed; анонімізація не є транзакцією; Git backup містить лише committed seed і код. Цілі production RTO<=60 хв/RPO<=15 хв залишаються проектними до появи persistence та виміряного restore drill.

Критерій перегляду: потреба зберігати користувацькі зміни після restart, масштабувати workers або довести обмежений RPO. Тоді створити ADR-0003 чи наступний вільний номер, а тут змінити лише lifecycle-статус на `Superseded by ADR-XXXX` і додати зв’язок, зберігши первинний текст рішення.

## Links and evidence

- [Repository source](../../../app/export/repository.py) — singleton і seed.
- [SDD Repository](../../sdd.md#repository), [модель даних](../../sdd.md#data-model).
- [ISD Repository](../../isd.md#repository), [RTO/RPO](../../isd.md#recovery-objectives).
- [ADR-0002](0002-immutable-shipping-contracts.md) — локальна незмінність DTO не надає сховищу персистентності.
