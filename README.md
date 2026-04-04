# SchedScope

A Linux kernel scheduler experimentation framework running inside QEMU.

The goal was to go beyond reading about CFS — to instrument it, modify it, measure the effect, and understand the trade-offs from inside the kernel.

---

## What This Project Does

- Boots a custom-built Linux 6.6 kernel inside QEMU
- Instruments `pick_next_task_fair()` with structured `[SCHED_TRACE]` events
- Runs controlled CPU-bound and IO-bound workloads via config files
- Collects, normalizes, and analyzes scheduling traces
- Compares baseline CFS against a modified vruntime placement policy
- Generates metrics and plots per run

---

## The Modification

**File:** `linux/kernel/sched/fair.c`

```c
se->vruntime += nice * 50000;
```

Applied at task enqueue. The effect:

- Tasks with lower nice values (higher priority) get a smaller vruntime → selected earlier by the red-black tree
- Tasks with higher nice values (lower priority) get a larger vruntime → pushed back in the run queue

This biases placement at enqueue time, making priority re-enter competition earlier without touching the core CFS pick logic.

---

## Measured Results

| Metric | Baseline | Modified |
|---|---|---|
| Context switches | 13,478 | 22,164 |
| Preemptions | 6,777 | 11,217 |
| Trace duration (ns) | 7,179,319,944 | 6,626,954,468 |
| Fairness index | 0.2399 | 0.2184 |

**Observation:** The modified scheduler showed +64% context switches and +66% preemptions, with a slight drop in the fairness index. The shorter trace duration suggests faster task turnover. These results come from a small number of runs and are presented as initial observations, not final claims.

**Trade-off:** Increased scheduling activity improves responsiveness for high-priority tasks but adds overhead and reduces fairness across the board.

---

## Architecture

```
Build kernel → Boot in QEMU → Run workloads → Collect traces
     ↓
Filter [SCHED_TRACE] events → Normalize → Compute metrics
     ↓
CSV export → Plot generation → Baseline vs Modified comparison
```

Key components:

- `linux/kernel/sched/fair.c` — instrumented and modified scheduler
- `workloads/` — C programs for CPU-bound and IO-bound behavior
- `scripts/collect_trace_run.sh` — boots QEMU and captures trace output
- `scripts/analyze_trace.py` — parses events and computes metrics
- `scripts/benchmark_runner.py` — batch execution across configs
- `scripts/generate_plots.py` — Gantt timeline, latency, fairness plots

---

## Quick Start

```bash
# Build workloads
bash scripts/build_workloads.sh

# Build initramfs
bash scripts/build_initramfs.sh rootfs rootfs.cpio.gz

# Build kernel
make -C linux -j"$(nproc)" bzImage

# Run one trace collection
bash scripts/collect_trace_run.sh --run-name run_01

# Analyze
python3 scripts/analyze_trace.py results/run_01/sched_trace.log

# Batch benchmark
python3 scripts/benchmark_runner.py --manifest benchmarks/baseline_runs.json

# Generate plots
python3 scripts/generate_plots.py results/run_01 --summary-csv results/summary.csv
```

---

## Repository Layout

```
schedscope/
├── linux/              # Kernel source + scheduler modifications
├── rootfs/             # BusyBox-based guest filesystem
├── workloads/          # Workload sources and configs
├── scripts/            # Build, run, analysis, benchmark, plotting
├── analysis/           # Trace parsing and metric computation
├── benchmarks/         # Experiment manifests
├── results/            # Collected run outputs
├── plots/              # Generated visual artifacts
└── docs/               # Architecture, experiments, AI workflow, lessons learned
```

---

## Outputs Per Run

```
results/<run_name>/
├── raw.log
├── sched_trace.log
├── normalized_events.jsonl
├── normalized_events.csv
├── metrics_summary.json
├── metrics_summary.txt
├── timeline_data.csv
└── per_task_metrics.csv

plots/<run_name>/
├── timeline.png
├── latency.png
└── fairness.png
```

---

## What I Would Do Differently

- Use custom tracepoints (`TRACE_EVENT`) instead of `trace_printk` — lower overhead and cleaner output
- Add an explicit task completion event to the trace schema to avoid inferred turnaround times
- Run experiments with more controlled workload isolation to reduce noise in the fairness metrics
- Test the modification under multi-core scheduling to observe per-core queue effects

---

## Docs

- [Architecture Overview](docs/architecture.md)
- [Experiments Guide](docs/experiments.md)
- [AI Workflow Notes](docs/ai_workflow.md)
- [Lessons Learned](docs/lessons_learned.md)
