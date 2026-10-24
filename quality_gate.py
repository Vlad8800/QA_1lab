"""Reject staged Python methods whose Radon cyclomatic complexity exceeds 10."""

import subprocess
import sys

from radon.complexity import cc_visit


LIMIT = 10
RED = "\033[31m"
RESET = "\033[0m"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], stderr=subprocess.STDOUT)


def staged_python_files() -> list[str]:
    paths = git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACM")
    return [p.decode("utf-8") for p in paths.split(b"\0") if p.endswith(b".py")]


def main() -> int:
    try:
        files = staged_python_files()
        violations = []
        for path in files:
            # Read the index blob: unstaged working-tree edits cannot bypass this gate.
            source = git("show", f":{path}").decode("utf-8-sig")
            for block in cc_visit(source):
                methods = block.methods if hasattr(block, "methods") else [block]
                for method in methods:
                    if method.complexity > LIMIT:
                        violations.append((path, method.name, method.lineno, method.complexity))
    except (OSError, UnicodeError, ValueError, SyntaxError, subprocess.CalledProcessError) as exc:
        print(f"{RED}[FAIL] Quality gate could not scan staged code: {exc}{RESET}", file=sys.stderr)
        return 1

    if violations:
        for path, name, line, complexity in violations:
            print(
                f"{RED}[FAIL] {path}:{line} {name}: CC={complexity} > {LIMIT}{RESET}",
                file=sys.stderr,
            )
        print(f"{RED}[BLOCKED] Commit rejected by cyclomatic complexity gate.{RESET}", file=sys.stderr)
        return 1

    print(f"[PASS] {len(files)} staged Python file(s); all methods have CC <= {LIMIT}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
