---
owner: Vlad8800
status: published
review_date: 2027-05-19
tags: [api]
---

# API — інтерактивний контракт

Єдине джерело істини: [openapi.yaml](openapi.yaml). Swagger UI читає цей файл без копії схем.
Контракт охоплює три операції; решта демонстраційного API ще не входить до цього контракту.

<swagger-ui src="openapi.yaml"/>

Для Try it out запустіть API за [інструкцією](../developer/local.md), розгорніть операцію,
натисніть Try it out → Execute. Приклад для розрахунку: UA, один товар ціною 25 і кількістю 2.
Локальний сервер для перевірки — http://127.0.0.1:8000; публічний backend не розгортається.

SDK генерується командою:

```shell
openapi-generator-cli generate -i docs/api/openapi.yaml -g python -o sdk-client --additional-properties=packageName=qa1lab_client
```

[[architecture/sdd|SDD]] · [[developer/reference|Docstrings]]
