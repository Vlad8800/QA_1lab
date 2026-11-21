---
owner: Vlad8800
status: published
review_date: 2027-02-18
tags: [ops]
---

# RFC-001 — контрольована деградація export

Вимога REQ-OPS-001. ITIL normal, ризик 2×3=6/25. Мета: при OSError repository
повертати 503 з Retry-After=30 без приватної діагностики, після recovery — 200.
Стан: Implemented locally / Pending student acceptance.
Повна форма: docs/changes/RFC-001.md, Impact Analysis та CCB-001 у тій самій папці.
Workflow: Draft → Assessment → Pending CCB → Approved / Rejected → Implemented → Closed.
Відкат: revert change-коміту, зміна даних відсутня. Production rollout не виконано.
