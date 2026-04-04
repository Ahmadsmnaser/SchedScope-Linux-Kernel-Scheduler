# Experiments Guide

## Workload Definitions

Available workload programs:

- [cpu_bound.c](/home/ahmad/.ssh/Scheduler_sh/workloads/src/cpu_bound.c): busy-loop task for CPU pressure
- [sleep_burst.c](/home/ahmad/.ssh/Scheduler_sh/workloads/src/sleep_burst.c): alternating burst and sleep behavior

Primary config:

- [mixed_workload.json](/home/ahmad/.ssh/Scheduler_sh/workloads/configs/mixed_workload.json)

This workload mixes:

- one normal-priority CPU-bound task
- one lower-priority CPU-bound task
- one sleep/burst task

## Experiment Setup

Baseline run:

```bash
python3 scripts/benchmark_runner.py --manifest benchmarks/baseline_runs.json --summary results/summary.csv
```

Modified scheduler run:

```bash
python3 scripts/benchmark_runner.py --manifest benchmarks/phase8_modified_runs.json --summary results/phase8_modified_summary.csv
```

Single-run flow:

```bash
bash scripts/collect_trace_run.sh --run-name run_01
python3 scripts/analyze_trace.py results/run_01/sched_trace.log
python3 scripts/generate_plots.py results/run_01
```

## Outputs

Per-run files:

- `raw.log`
- `sched_trace.log`
- `normalized_events.jsonl`
- `normalized_events.csv`
- `metrics_summary.json`
- `metrics_summary.txt`
- `timeline_data.csv`
- `per_task_metrics.csv`

Batch files:

- `results/summary.csv`
- `results/phase8_modified_summary.csv`

Plots:

- `plots/<run_name>/timeline.png`
- `plots/<run_name>/latency.png`
- `plots/<run_name>/fairness.png`

## Results And Observations

Observed baseline smoke run summary:

- [results/phase7_smoke_summary.csv](/home/ahmad/.ssh/Scheduler_sh/results/phase7_smoke_summary.csv)

Observed modified scheduler summary:

- [results/phase8_modified_summary.csv](/home/ahmad/.ssh/Scheduler_sh/results/phase8_modified_summary.csv)

Current high-level observation:

- the Phase 8 vruntime placement bias increased scheduling activity in the recorded smoke comparison
- the modified run showed more context switches and preemptions than the earlier baseline smoke run
- this is still an exploratory result, not a final claim, because it comes from a small number of runs and workload timing can still vary

## Recommended Next Experiment Improvements

- run multiple baseline and modified repetitions with the same manifest structure
- add explicit workload variants instead of relying on one mixed profile
- add a stronger task identity mapping if per-task workload attribution becomes important
