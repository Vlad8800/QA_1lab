"""Join Radon complexity with 90-day per-file Git commit counts."""

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


def command(*args):
    return subprocess.run(args, check=True, stdout=subprocess.PIPE).stdout


def tracked_python_files():
    paths = command("git", "ls-files", "-z", "--", "*.py").decode("utf-8").split("\0")
    return sorted(path for path in paths if path and Path(path).is_file())


def churn_counts(since):
    # --no-renames counts edits under the current path; one name per commit.
    output = command(
        "git", "log", "--since=" + since, "--no-renames", "--format=", "--name-only", "-z", "--"
    ).decode("utf-8")
    return Counter(path for path in output.split("\0") if path)


def risk_category(max_cc, commits, cc_threshold, churn_threshold):
    complex_file = max_cc > cc_threshold
    active_file = commits >= churn_threshold
    if complex_file and active_file:
        return "Hotspot"
    if complex_file:
        return "Sleeping Danger"
    if active_file:
        return "Active Development"
    return "Stable Code"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/hotspots"))
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--cc-threshold", type=int, default=10)
    parser.add_argument("--churn-threshold", type=int, default=5)
    args = parser.parse_args()
    if args.days < 1 or args.churn_threshold < 1 or args.cc_threshold < 0:
        parser.error("thresholds and period must be positive")

    files = tracked_python_files()
    if not files:
        parser.error("no tracked Python files found")
    since = (datetime.now(timezone.utc) - timedelta(days=args.days)).isoformat()
    cc = json.loads(command(sys.executable, "-m", "radon", "cc", "-j", "-s", *files))
    hal = json.loads(command(sys.executable, "-m", "radon", "hal", "-j", *files))
    churn = churn_counts(since)
    rows = []
    for path in files:
        blocks = cc.get(path, [])
        max_cc = max((block["complexity"] for block in blocks), default=0)
        count = churn[path]
        rows.append({
            "file": path,
            "max_cc": max_cc,
            "halstead_effort": round(hal.get(path, {}).get("total", {}).get("effort", 0), 2),
            "commits_90d": count,
            "category": risk_category(max_cc, count, args.cc_threshold, args.churn_threshold),
        })
    rows.sort(key=lambda row: (-row["commits_90d"], -row["max_cc"], row["file"]))

    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / "radon_cc.json").write_text(json.dumps(cc, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "radon_halstead.json").write_text(json.dumps(hal, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": command("git", "rev-parse", "HEAD").decode().strip(),
        "period_days": args.days,
        "since_utc": since,
        "cc_high_when_gt": args.cc_threshold,
        "churn_high_when_gte": args.churn_threshold,
        "files": rows,
    }
    (output / "hotspots.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output / "hotspots.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    churn_log = "\n".join(f"{row['commits_90d']:>3}  {row['file']}" for row in rows)
    (output / "churn_90d.txt").write_text(churn_log + "\n", encoding="utf-8")
    print("Git command: git log --since=" + since + " --no-renames --format= --name-only -z --")
    print(churn_log)
    print(f"Scanned {len(files)} tracked Python files; reports in {output}")


if __name__ == "__main__":
    main()
