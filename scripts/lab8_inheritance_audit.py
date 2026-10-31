"""Measure local DIT, public interface and overrides for shipping policy classes."""

import argparse
import ast
import json
from pathlib import Path
from xml.sax.saxutils import escape


def class_name(node):
    return node.id if isinstance(node, ast.Name) else None


def own_public_methods(node):
    return {item.name for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not item.name.startswith("_")}


def parent_names(node, classes):
    return [name for base in node.bases if (name := class_name(base)) in classes]


def inherited_methods(name, classes):
    inherited = set()
    for parent in parent_names(classes[name], classes):
        inherited |= own_public_methods(classes[parent]) | inherited_methods(parent, classes)
    return inherited


def depth(name, classes):
    parents = parent_names(classes[name], classes)
    return 1 + max((depth(parent, classes) for parent in parents), default=0)


def injected_dependencies(node, classes):
    dependencies = set()
    for method in node.body:
        if isinstance(method, ast.FunctionDef) and method.name == "__init__":
            for argument in method.args.args:
                if (name := class_name(argument.annotation)) in classes:
                    dependencies.add(name)
    return sorted(dependencies)


def audit(classes):
    result = []
    for name, node in classes.items():
        own = own_public_methods(node)
        inherited = inherited_methods(name, classes)
        result.append({
            "class": name, "dit_root_is_1": depth(name, classes),
            "pim_public_methods": len(own | inherited),
            "added_public_methods": len(own - inherited),
            "overridden_methods": sorted(own & inherited),
            "parent_classes": parent_names(node, classes),
            "injected_components": injected_dependencies(node, classes),
            "public_method_names": sorted(own | inherited),
        })
    return result


def write_svg(rows, output):
    width, height = 1100, 640
    y_by_name = {row["class"]: 90 + index * 180 for index, row in enumerate(rows)}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<text x="35" y="40" font-family="Arial" font-size="25" fill="#0f172a">Lab 8 vertical architecture audit</text>',
    ]
    for row in rows:
        y = y_by_name[row["class"]]
        parts.extend([
            f'<rect x="270" y="{y}" width="560" height="100" rx="12" fill="#dbeafe" stroke="#60a5fa" stroke-width="2"/>',
            f'<text x="290" y="{y + 37}" font-family="Arial" font-size="21" fill="#0f172a">{escape(row["class"])}</text>',
            f'<text x="290" y="{y + 69}" font-family="Arial" font-size="17" fill="#334155">DIT={row["dit_root_is_1"]}  PIM={row["pim_public_methods"]}  Overridden={len(row["overridden_methods"])}</text>',
        ])
        for related in row["parent_classes"] + row["injected_components"]:
            label = "inherits" if related in row["parent_classes"] else "contains / injected"
            target_y = y_by_name[related] + 100
            parts.extend([
                f'<line x1="550" y1="{target_y}" x2="550" y2="{y}" stroke="#475569" stroke-width="3"/>',
                f'<text x="570" y="{(target_y + y) // 2}" font-family="Arial" font-size="16" fill="#475569">{label}</text>',
            ])
    parts.append('</svg>')
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("app/shipping_policy.py"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    tree = ast.parse(args.source.read_text(encoding="utf-8"), filename=str(args.source))
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    rows = audit(classes)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "inheritance_metrics.json").write_text(
        json.dumps({"source": str(args.source), "dit_definition": "root class = 1", "classes": rows},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_svg(rows, args.output_dir / "inheritance_graph.svg")
    for row in rows:
        print(row["class"], row["dit_root_is_1"], row["pim_public_methods"], len(row["overridden_methods"]))


if __name__ == "__main__":
    main()
