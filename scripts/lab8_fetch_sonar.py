"""Save reproducible SonarCloud REST responses for lab 8 task 1.

The project is public. No token is required for these read-only requests.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


HOST = "https://sonarcloud.io"
FILES = ("app/services.py", "app/export/repository.py", "app/consent/schemas.py")
REQUIRED_OO_KEYS = (
    "class_complexity", "coupling_between_objects", "cohesion_in_methods",
    "lcom4", "mhf", "ahf", "cof", "dit",
)


def fetch(path, params):
    url = HOST + path + "?" + urlencode(params)
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "lab8-metric-audit/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            status = response.status
            body = response.read().decode("utf-8")
    except HTTPError as error:
        status = error.code
        body = error.read().decode("utf-8")
    return {"request_url": url, "http_status": status, "body": json.loads(body)}


def collect_responses(project_key):
    catalog = fetch("/api/metrics/search", {"ps": 500})
    if catalog["http_status"] != 200:
        raise RuntimeError(f"Metric catalog failed: HTTP {catalog['http_status']}")
    available = {metric["key"] for metric in catalog["body"]["metrics"]}
    supported = [key for key in ("complexity", "cognitive_complexity", "ncloc") if key in available]
    result = {
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_key": project_key,
        "metric_catalog": {
            "request_url": catalog["request_url"],
            "http_status": catalog["http_status"],
            "total": catalog["body"]["total"],
            "available_keys": sorted(available),
            "required_oo_keys_absent": [key for key in REQUIRED_OO_KEYS if key not in available],
        },
        "latest_analysis": fetch("/api/project_analyses/search", {"project": project_key, "ps": 1}),
        "project_measures": fetch("/api/measures/component", {
            "component": project_key, "metricKeys": ",".join(supported),
        }),
        "file_measures": {},
        "unsupported_oo_request": fetch("/api/measures/component", {
            "component": project_key + ":" + FILES[0],
            "metricKeys": "class_complexity,coupling_between_objects,lcom4",
        }),
    }
    for path in FILES:
        result["file_measures"][path] = fetch("/api/measures/component", {
            "component": project_key + ":" + path,
            "metricKeys": ",".join(supported),
        })
    return result


def print_summary(result):
    for path, response in result["file_measures"].items():
        if response["http_status"] != 200:
            raise RuntimeError(f"File request failed for {path}: HTTP {response['http_status']}")
        measures = {item["metric"]: item["value"] for item in response["body"]["component"]["measures"]}
        print(path, measures)
    print("Unavailable OO keys:", ", ".join(result["metric_catalog"]["required_oo_keys_absent"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-key", default="Vlad8800_QA_1lab")
    parser.add_argument("--output-dir", type=Path, default=Path("docs/lab8/task1-artifacts"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = collect_responses(args.project_key)
    output = args.output_dir / "sonar_api_baseline.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    print_summary(result)


if __name__ == "__main__":
    main()
