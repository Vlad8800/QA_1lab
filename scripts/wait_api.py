import time
import httpx

for attempt in range(40):
    try:
        if httpx.get('http://127.0.0.1:8000/api/v1/shipping/policy', timeout=1, trust_env=False).status_code == 200:
            break
    except httpx.HTTPError:
        pass
    time.sleep(0.25)
else:
    raise SystemExit('API did not become ready within 10 seconds')
