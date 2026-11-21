---
owner: Vlad8800
status: published
review_date: 2027-02-18
tags: [ops]
---

# Каталог алертів

Це специфікація для налаштування моніторингу. Підключення реального Grafana/Prometheus
не підтверджено; у drill тригери перевіряються тестовими подіями.

| Назва | Умова | Серйозність | Відповідальна роль | Runbook |
| --- | --- | --- | --- | --- |
| EXPORT_FAILURE | Частка 5xx авторизованого export > 1% за 5 хв, не менше 20 запитів | SEV-2 | L2/SRE | [RB-001](../runbooks/RB-001.md) |
| API_UNAVAILABLE | 3 послідовні невдалі проби /api/v1/shipping/policy з інтервалом 30 с | SEV-1 | SRE on-call | [RB-001](../runbooks/RB-001.md) |
| RESTORE_DRILL_FAILED | Останній щотижневий drill має code != 0 або відсутній понад 8 діб | SEV-2 | Backup owner/SRE | [RB-001](../runbooks/RB-001.md) |
| EXPORT_LATENCY | Менше 99% export-запитів <= 300 мс за 5 хв, n >= 20 | SEV-3 | L2 | [RB-001](../runbooks/RB-001.md) |

Для всіх алертів: не включати персональні дані в labels; групувати за сервісом;
dedup 5 хв; resolve після 5 хв без умови; планові drill мають maintenance label.
