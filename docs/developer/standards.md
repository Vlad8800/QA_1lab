---
owner: Vlad8800
status: published
review_date: 2027-02-18
tags: [ops]
---

# Стандарти коду

Python: відступ 4 пробіли, імена snake_case, типізація публічних функцій, відокремлення HTTP-маршрутів від бізнес-логіки.
Перевірка стилю: python -m flake8 app; поведінки: python -m pytest tests.
Новий тест перевіряє спостережувану поведінку, а не повторює реалізацію.
Коміти: Conventional Commits (feat, fix, test, docs).
Логи не містять сирих персональних даних; секрети не зберігаємо в Git.

[[developer/contributing|Рев’ю]] · [[architecture/sdd|Залежності]]
