#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
DEFAULT_MANIFEST = ROOT / "benchmarks" / "baseline_runs.json"


def load_manifest(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    experiments = data.get("experiments", [])
    if not experiments:
        raise SystemExit(f"no experiments found in manifest: {path}")
    return experiments


def run_command(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, cwd=ROOT)


def read_metrics_summary(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    trace = data.get("trace_summary", {})
    agg = data.get("aggregate_metrics", {})
    return {
        "event_count": trace.get("event_count"),
        "trace_duration_ns": trace.get("trace_duration_ns"),
        "context_switches": agg.get("context_switches"),
        "preemptions": agg.get("preemptions"),
        "cpu_utilization_estimate": agg.get("cpu_utilization_estimate"),
        "throughput_tasks_per_sec_inferred": agg.get("throughput_tasks_per_sec_inferred"),
        "fairness_jain_runtime_user_tasks": agg.get("fairness_jain_runtime_user_tasks"),
        "completed_tasks_inferred": agg.get("completed_tasks_inferred"),
    }


def write_summary(rows: list[dict], output_path: Path) -> None:
    fieldnames = [
        "experiment",
        "run_name",
        "kernel_append",
        "event_count",
        "trace_duration_ns",
        "context_switches",
        "preemptions",
        "cpu_utilization_estimate",
        "throughput_tasks_per_sec_inferred",
        "fairness_jain_runtime_user_tasks",
        "completed_tasks_inferred",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def main() -> int:
    parser = argparse.ArgumentParser(description="Run repeatable SchedScope benchmark batches")
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="Path to benchmark manifest JSON",
    )
    parser.add_argument(
        "--summary",
        default=str(RESULTS_DIR / "summary.csv"),
        help="Path to output summary CSV",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    summary_path = Path(args.summary).resolve()
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    experiments = load_manifest(manifest_path)
    summary_rows: list[dict] = []

    for experiment in experiments:
        experiment_name = experiment["name"]
        repeat = int(experiment.get("repeat", 1))
        kernel_append = experiment.get("kernel_append", "")
        timeout_seconds = int(experiment.get("timeout_seconds", 60))

        for run_index in range(1, repeat + 1):
            run_name = f"{experiment_name}_{run_index:02d}"
            collect_cmd = [
                "bash",
                str(ROOT / "scripts" / "collect_trace_run.sh"),
                "--run-name",
                run_name,
                "--timeout",
                str(timeout_seconds),
            ]
            if kernel_append:
                collect_cmd.extend(["--kernel-append", kernel_append])

            run_command(collect_cmd)

            trace_path = RESULTS_DIR / run_name / "sched_trace.log"
            run_command(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "analyze_trace.py"),
                    str(trace_path),
                    "--output-dir",
                    str(RESULTS_DIR / run_name),
                ]
            )

            metrics = read_metrics_summary(RESULTS_DIR / run_name / "metrics_summary.json")
            summary_rows.append(
                {
                    "experiment": experiment_name,
                    "run_name": run_name,
                    "kernel_append": kernel_append,
                    **metrics,
                }
            )

    write_summary(summary_rows, summary_path)
    print(f"Wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
