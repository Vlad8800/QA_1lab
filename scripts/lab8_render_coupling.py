"""Render a reproducible coupling matrix and focus graph from AST evidence."""

import argparse
import csv
import json
from pathlib import Path
from xml.sax.saxutils import escape


def write_matrix(rows, output):
    names = [row["class"] for row in rows]
    relations = {row["class"]: set(row["coupled_classes"]) for row in rows}
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["source / target", *names])
        for name in names:
            writer.writerow([name, *(int(target in relations[name]) for target in names)])


def write_focus_svg(row, output):
    targets = row["coupled_classes"]
    height = max(600, 70 + len(targets) * 45)
    center_y = height // 2
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1450" height="{height}" viewBox="0 0 1450 {height}">',
        '<rect width="1450" height="100%" fill="#f8fafc"/>',
        '<text x="35" y="38" font-family="Arial" font-size="24" fill="#0f172a">Lab 8 dependency graph — explicit project-class references</text>',
        f'<rect x="35" y="{center_y - 48}" width="500" height="96" rx="12" fill="#7f1d1d"/>',
        f'<text x="52" y="{center_y - 8}" font-family="Arial" font-size="19" fill="white">{escape(row["class"].split(".")[-1])}</text>',
        f'<text x="52" y="{center_y + 22}" font-family="Arial" font-size="15" fill="white">CBO proxy = {len(targets)}; WMC = {row["wmc_radon_sum"]}; LCOM4 proxy = {row["lcom4_ast_proxy"]}</text>',
    ]
    for index, target in enumerate(targets):
        y = 65 + index * 45
        parts.extend([
            f'<line x1="535" y1="{center_y}" x2="740" y2="{y + 16}" stroke="#64748b" stroke-width="1.6"/>',
            f'<rect x="740" y="{y}" width="675" height="32" rx="6" fill="#dbeafe" stroke="#93c5fd"/>',
            f'<text x="752" y="{y + 22}" font-family="Arial" font-size="15" fill="#0f172a">{escape(target)}</text>',
        ])
    parts.append('</svg>')
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--focus", required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(args.input.read_text(encoding="utf-8"))
    rows = data["all_classes"]
    focus = next(row for row in rows if row["class"] == args.focus)
    write_matrix(rows, args.output_dir / "coupling_matrix.csv")
    write_focus_svg(focus, args.output_dir / "coupling_graph.svg")
    print(args.output_dir, focus["class"], focus["cbo_project_class_reference_proxy"])


if __name__ == "__main__":
    main()
