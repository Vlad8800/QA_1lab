# Контрольований FAIL — Shotgun Surgery

У залежному `ConsentManagementService.grant_consent` перейменовано лише параметр `policy_version` на `agreement_version`. Моноліт `PrivacyOperationsGodObject.grant` і HTTP-маршрут продовжують передавати старий іменований аргумент. У Python це спричиняє `TypeError` до виконання бізнес-логіки.

Команда запуску в Python 3.11 Docker-контейнері:

```powershell
docker run --rm -v "${PWD}:/workspace" -w /workspace --entrypoint python lab8-test-env:latest -m pytest tests/test_lab8_architecture.py tests/test_consent_management.py -q --tb=short -p no:warnings
```

У [`pytest.log`](pytest.log) видно `4 failed, 5 passed` і точні місця поломки. [`result.txt`](result.txt) містить код завершення `1`. Це навмисно зафіксований проміжний стан; фінальна гілка має завершитися PASS-комітом.
