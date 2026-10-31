"""Render the verified task 3 Git history as a shareable image source."""

import subprocess
from pathlib import Path
from xml.sax.saxutils import escape


OUTPUT = Path("docs/lab8/task3-artifacts/git_history.svg")
RANGE = "0a44142..91beb7c"


def main():
    lines = subprocess.check_output(
        ["git", "log", "--graph", "--oneline", RANGE], encoding="utf-8"
    ).splitlines()
    if len(lines) != 3:
        raise RuntimeError(f"Expected Baseline, FAIL, PASS; found {len(lines)} commits")
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="310" viewBox="0 0 1280 310">',
        '<rect width="100%" height="100%" fill="#0d1117"/>',
        '<text x="30" y="48" font-family="Consolas,monospace" font-size="24" fill="#e6edf3">git log --graph --oneline 0a44142..91beb7c</text>',
    ]
    for index, line in enumerate(lines):
        color = "#3fb950" if "PASS" in line else "#f85149" if "FAIL" in line else "#79c0ff"
        parts.append(
            f'<text x="40" y="{105 + index * 65}" font-family="Consolas,monospace" '
            f'font-size="21" fill="{color}">{escape(line)}</text>'
        )
    parts.append('</svg>')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
