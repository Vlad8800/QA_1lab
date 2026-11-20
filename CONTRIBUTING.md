---
owner: Vlad8800
status: published
review_date: 2027-02-18
tags: [ops]
---

# Внесення змін

## Definition of Done — docs-or-don’t-merge

- [ ] Змінена публічна поведінка описана в docs/.
- [ ] Зміни API спочатку погоджено в docs/api/openapi.yaml; реалізацію перевірено контрактним тестом.
- [ ] Оновлено CHANGELOG.md, owner, status, review_date зачеплених сторінок.
- [ ] Spectral, markdownlint, аудит дат і mkdocs build --strict проходять.
- [ ] Власник з CODEOWNERS виконав рев’ю; merge дозволений після успішних required checks.

CODEOWNERS призначає рев’юера. Для фізичного блокування merge в GitHub Rulesets слід увімкнути
Require a pull request, Require review from Code Owners і required check «docs-build».
Власник PR не може затвердити власний PR: потрібен другий уповноважений учасник.

ADR не переписуємо: нове рішення має новий номер; попереднє отримує Superseded і посилання.
Документи з простроченим review_date спочатку перевіряє owner; deprecated потребує replacement.
Мажорний випуск бази знань: git tag docs-v1.0; наступний — docs-v2.0.

[[developer/standards|Стандарти]] · [[architecture/adr/README|Рішення]]
