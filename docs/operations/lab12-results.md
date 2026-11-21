---
owner: Vlad8800
status: published
review_date: 2027-02-18
tags: [ops]
---

# ЛР12 — результати та межі готовності

Ізольований інцидент: FAIL 5×500; після патча 5×503/Retry-After; recovery 3×200.
Restore drill конфігурації: PASS, 0.064 с, RTO target 900 с.
Підсумковий pytest exit code: 0. Логи зберігаються в Lab12/evidence.
Зовнішній RFC tracker: GitHub 403; issue не створено.
Власний RCA/CAPA: очікується від студента. Моніторинг, off-site 3-2-1 та CCB —
задокументовані навчальні моделі, не розгорнуті production сервіси.
