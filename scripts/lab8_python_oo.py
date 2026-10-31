"""Compute explicit, conservative Python AST proxies for CK/MOOD metrics.

These are local estimates, never SonarCloud measures. See lab 8 report for definitions.
"""

import ast
import json
from collections import defaultdict
from pathlib import Path

from radon.complexity import cc_visit


ROOT = Path("app")
SELECTED = ("app/services.py", "app/export/repository.py", "app/consent/schemas.py")
OUTPUT = Path("docs/lab8/task1-artifacts/python_oo_estimates.json")


def method_uses(method):
    attributes, calls = set(), set()
    for node in ast.walk(method):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
            if isinstance(getattr(node, "ctx", None), ast.Load):
                attributes.add(node.attr)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "self":
                calls.add(node.func.attr)
    return attributes, calls


def lcom4(methods):
    if not methods:
        return 0
    names = [method.name for method in methods]
    uses = [method_uses(method) for method in methods]
    parent = list(range(len(methods)))

    def root(index):
        while parent[index] != index:
            index = parent[index]
        return index

    for left in range(len(methods)):
        for right in range(left + 1, len(methods)):
            shared_fields = uses[left][0] & uses[right][0] - set(names)
            direct_call = names[right] in uses[left][1] or names[left] in uses[right][1]
            if shared_fields or direct_call:
                parent[root(right)] = root(left)
    return len({root(index) for index in range(len(methods))})


def fields_of(class_node):
    fields = set()
    for node in ast.walk(class_node):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for child in ast.walk(target):
                    if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name):
                        if child.value.id == "self":
                            fields.add(child.attr)
    return fields


def discover_classes():
    modules = {}
    classes = {}
    names = defaultdict(set)
    for path in sorted(ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        module = ".".join(path.with_suffix("").parts)
        modules[module] = (str(path).replace("\\", "/"), tree, source)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                identifier = module + "." + node.name
                classes[identifier] = (module, node)
                names[node.name].add(identifier)
    return modules, classes, names


def class_references(class_node, identifier, names):
    refs = set()
    for node in ast.walk(class_node):
        if isinstance(node, ast.Name) and len(names[node.id]) == 1:
            refs.update(names[node.id])
        elif isinstance(node, ast.Attribute) and len(names[node.attr]) == 1:
            refs.update(names[node.attr])
    refs.discard(identifier)
    return refs


def class_wmc(source, class_node):
    block = next((item for item in cc_visit(source) if item.letter == "C" and item.name == class_node.name and item.lineno == class_node.lineno), None)
    return sum(method.complexity for method in block.methods) if block else None


def visibility_counts(methods, fields):
    visible_methods = [method for method in methods if not method.name.startswith("__")]
    visible_fields = [field for field in fields if not (field.startswith("__") and field.endswith("__"))]
    return {
        "visible_method_count": len(visible_methods),
        "hidden_method_count": sum(method.name.startswith("_") for method in visible_methods),
        "visible_field_count": len(visible_fields),
        "hidden_field_count": sum(field.startswith("_") for field in visible_fields),
    }


def analyze_class(identifier, module, class_node, modules, names):
    path, _, source = modules[module]
    methods = [node for node in class_node.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    fields = fields_of(class_node)
    refs = class_references(class_node, identifier, names)
    result = {
        "class": identifier, "file": path, "wmc_radon_sum": class_wmc(source, class_node),
        "cbo_project_class_reference_proxy": len(refs),
        "lcom4_ast_proxy": lcom4(methods),
        "method_count": len(methods), "fields": sorted(fields),
        "coupled_classes": sorted(refs),
    }
    result.update(visibility_counts(methods, fields))
    return result


def project_stats(results):
    n = len(results)
    methods = sum(row["visible_method_count"] for row in results)
    hidden_methods = sum(row["hidden_method_count"] for row in results)
    fields = sum(row["visible_field_count"] for row in results)
    hidden_fields = sum(row["hidden_field_count"] for row in results)
    edges = sum(row["cbo_project_class_reference_proxy"] for row in results)
    return {
        "class_count": n, "method_count": methods, "hidden_method_count": hidden_methods,
        "field_count": fields, "hidden_field_count": hidden_fields,
        "directed_class_reference_edges": edges,
        "mhf_python_convention_proxy": round(hidden_methods / methods, 4) if methods else None,
        "ahf_python_convention_proxy": round(hidden_fields / fields, 4) if fields else None,
        "cof_project_reference_proxy": round(edges / (n * (n - 1)), 4) if n > 1 else None,
    }


def make_output(results):
    return {
        "definitions": {
            "wmc_radon_sum": "Sum of Radon cyclomatic complexity for methods in each class.",
            "cbo_project_class_reference_proxy": "Distinct same-project classes named in the class AST; dynamic calls and ambiguous names may be missed.",
            "lcom4_ast_proxy": "Connected components of instance methods sharing self fields or calling each other; 1 is the cohesive ideal, 0 means no methods.",
            "mhf_python_convention_proxy": "Underscore-prefixed methods / methods excluding double-underscore methods.",
            "ahf_python_convention_proxy": "Underscore-prefixed instance fields / instance fields excluding double-underscore fields.",
            "cof_project_reference_proxy": "Directed same-project class reference edges / N(N-1).",
        },
        "project": project_stats(results),
        "selected_files": {
            path: [result for result in results if result["file"] == path] for path in SELECTED
        },
        "all_classes": results,
    }


def main():
    modules, classes, names = discover_classes()
    results = [analyze_class(identifier, module, node, modules, names)
               for identifier, (module, node) in sorted(classes.items())]
    output = make_output(results)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)
    print("Project:", output["project"])
    for path, rows in output["selected_files"].items():
        print(path, [(row["class"], row["wmc_radon_sum"], row["cbo_project_class_reference_proxy"], row["lcom4_ast_proxy"]) for row in rows])


if __name__ == "__main__":
    main()
