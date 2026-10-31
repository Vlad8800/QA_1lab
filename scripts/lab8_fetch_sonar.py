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


def measure_request(component, supported, branch):
    params = {"component": component, "metricKeys": ",".join(supported)}
    if branch:
        params["branch"] = branch
    return fetch("/api/measures/component", params)


def analysis_info(project_key, branch):
    if branch:
        return None, fetch("/api/project_branches/list", {"project": project_key})
    return fetch("/api/project_analyses/search", {"project": project_key, "ps": 1}), None


def catalog_info(catalog, available):
    return {
        "request_url": catalog["request_url"],
        "http_status": catalog["http_status"],
        "total": catalog["body"]["total"],
        "available_keys": sorted(available),
        "required_oo_keys_absent": [key for key in REQUIRED_OO_KEYS if key not in available],
    }


def collect_responses(project_key, branch, files):
    catalog = fetch("/api/metrics/search", {"ps": 500})
    if catalog["http_status"] != 200:
        raise RuntimeError(f"Metric catalog failed: HTTP {catalog['http_status']}")
    available = {metric["key"] for metric in catalog["body"]["metrics"]}
    supported = [key for key in ("complexity", "cognitive_complexity", "ncloc") if key in available]
    latest_analysis, branch_info = analysis_info(project_key, branch)
    result = {
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_key": project_key,
        "branch": branch or "main",
        "metric_catalog": catalog_info(catalog, available),
        "latest_analysis": latest_analysis,
        "branch_info": branch_info,
        "project_measures": measure_request(project_key, supported, branch),
        "file_measures": {},
        "unsupported_oo_request": measure_request(
            project_key + ":" + files[0],
            ("class_complexity", "coupling_between_objects", "lcom4"), branch,
        ),
    }
    for path in files:
        result["file_measures"][path] = measure_request(project_key + ":" + path, supported, branch)
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
    parser.add_argument("--branch", help="SonarCloud branch name; omit for the main branch")
    parser.add_argument("--file", action="append", dest="files", help="Source file path; may be repeated")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = collect_responses(args.project_key, args.branch, args.files or FILES)
    output = args.output_dir / f"sonar_api_{'pass' if args.branch else 'baseline'}.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    print_summary(result)


if __name__ == "__main__":
    main()
