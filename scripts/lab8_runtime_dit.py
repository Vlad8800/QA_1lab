"""Cross-check the lab 8 inheritance metrics against Python's runtime MRO."""

import importlib
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
BASELINE = Path("docs/lab8/task3-artifacts/baseline/shipping_policy_at_0110a85.txt")
OUTPUT = Path("docs/lab8/task3-artifacts/runtime_dit_validation.json")
NAMES = ("BaseShippingQuote", "RegionalShippingQuote", "ExpressHolidayShippingQuote")


def public_methods(cls):
    return {name for name, value in vars(cls).items() if not name.startswith("_") and callable(value)}


def runtime_metrics(namespace, module_name):
    rows = []
    for name in NAMES:
        cls = namespace[name]
        project_mro = [item for item in cls.__mro__ if item.__module__ == module_name]
        own = public_methods(cls)
        inherited = set().union(*(public_methods(parent) for parent in project_mro[1:]))
        rows.append({
            "class": name,
            "mro": [item.__name__ for item in cls.__mro__],
            "dit_root_is_1": len(project_mro),
            "pim_public_methods": len(own | inherited),
            "overridden_methods": sorted(own & inherited),
        })
    return rows


def main():
    baseline_namespace = {"__name__": "lab8_baseline"}
    source = BASELINE.read_text(encoding="utf-8-sig")
    exec(compile(source, str(BASELINE), "exec"), baseline_namespace)
    pass_module = importlib.import_module("app.shipping_policy")
    result = {
        "baseline_source": str(BASELINE),
        "baseline_commit": "0110a85",
        "pass_commit": "91beb7c",
        "baseline": runtime_metrics(baseline_namespace, "lab8_baseline"),
        "pass": runtime_metrics(vars(pass_module), pass_module.__name__),
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)
    for stage in ("baseline", "pass"):
        for row in result[stage]:
            print(stage, row["class"], row["dit_root_is_1"], len(row["overridden_methods"]))


if __name__ == "__main__":
    main()
