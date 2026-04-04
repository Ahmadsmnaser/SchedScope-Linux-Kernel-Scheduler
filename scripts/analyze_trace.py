#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.metrics import compute_metrics
from analysis.parser import parse_trace_file, write_csv, write_jsonl


def build_summary_text(metrics: dict) -> str:
    trace = metrics["trace_summary"]
    agg = metrics["aggregate_metrics"]
    lines = [
        f"events={trace['event_count']}",
        f"duration_ns={trace['trace_duration_ns']}",
        f"context_switches={agg.get('context_switches')}",
        f"preemptions={agg.get('preemptions')}",
        f"cpu_utilization_estimate={agg.get('cpu_utilization_estimate')}",
        f"fairness_jain_runtime_user_tasks={agg.get('fairness_jain_runtime_user_tasks')}",
        f"completed_tasks_inferred={agg.get('completed_tasks_inferred')}",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize and analyze SchedScope trace logs")
    parser.add_argument("trace_path", help="Path to sched_trace.log")
    parser.add_argument(
        "--output-dir",
        help="Directory for normalized events and metrics outputs",
    )
    args = parser.parse_args()

    trace_path = Path(args.trace_path).resolve()
    if not trace_path.is_file():
        raise SystemExit(f"trace file not found: {trace_path}")

    output_dir = Path(args.output_dir).resolve() if args.output_dir else trace_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    events = parse_trace_file(trace_path)
    metrics = compute_metrics(events)

    jsonl_path = output_dir / "normalized_events.jsonl"
    csv_path = output_dir / "normalized_events.csv"
    metrics_path = output_dir / "metrics_summary.json"
    summary_path = output_dir / "metrics_summary.txt"

    write_jsonl(events, jsonl_path)
    write_csv(events, csv_path)
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.write_text(build_summary_text(metrics), encoding="utf-8")

    print(f"Parsed {len(events)} events from {trace_path}")
    print(f"Wrote {jsonl_path}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {metrics_path}")
    print(f"Wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
