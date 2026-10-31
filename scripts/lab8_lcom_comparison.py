"""Compare operational-method cohesion at baseline and PASS Git states."""

import ast
import json
import subprocess
from pathlib import Path

from lab8_python_oo import lcom4


BASELINE_REF = "59b6318"
BASELINE_PATH = "app/consent/privacy_god_object.py"
PASS_PATH = Path("app/consent/architecture/workflows.py")
OUTPUT = Path("docs/lab8/task2-artifacts/lcom_comparison.json")


def class_cohesion(source, name):
    tree = ast.parse(source)
    node = next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == name)
    methods = [item for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
               and not item.name.startswith("__")]
    components = lcom4(methods)
    normalized = (components - 1) / (len(methods) - 1) if len(methods) > 1 else 0.0
    return {"operational_methods": len(methods), "lcom4_components": components,
            "normalized_lcom4_proxy": round(normalized, 4)}


def main():
    baseline = subprocess.check_output(
        ["git", "show", f"{BASELINE_REF}:{BASELINE_PATH}"], encoding="utf-8"
    )
    current = PASS_PATH.read_text(encoding="utf-8")
    result = {
        "definition": "Exclude constructors and dunder methods. Connect methods sharing read self-fields or direct self-calls. Normalized proxy=(components-1)/(methods-1); a single method scores 0.",
        "baseline_ref": BASELINE_REF,
        "baseline": class_cohesion(baseline, "PrivacyOperationsGodObject"),
        "pass": {name: class_cohesion(current, name) for name in (
            "ConsentWorkflow", "MarketingWorkflow", "ExportWorkflow", "ErasureWorkflow"
        )},
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
