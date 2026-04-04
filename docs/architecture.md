# Architecture Overview

## Purpose

SchedScope is built to study Linux scheduler behavior in a controlled and reproducible environment. The design keeps kernel tracing, workload execution, analysis, benchmarking, and visualization as separate steps so each stage is easier to validate.

## System Design

Main layers:

- kernel layer:
  - custom Linux kernel in [linux](/home/ahmad/.ssh/Scheduler_sh/linux)
  - scheduler traces emitted from `core.c` and `fair.c`
- guest layer:
  - BusyBox rootfs in [rootfs](/home/ahmad/.ssh/Scheduler_sh/rootfs)
  - guest workload and trace scripts under [rootfs/workloads](/home/ahmad/.ssh/Scheduler_sh/rootfs/workloads)
- host automation layer:
  - collection, analysis, benchmark, and plotting scripts in [scripts](/home/ahmad/.ssh/Scheduler_sh/scripts)
- analysis layer:
  - parser and metrics engine in [analysis](/home/ahmad/.ssh/Scheduler_sh/analysis)
- artifact layer:
  - run outputs in [results](/home/ahmad/.ssh/Scheduler_sh/results)
  - visual outputs in [plots](/home/ahmad/.ssh/Scheduler_sh/plots)

## Data Flow

1. The host builds `bzImage` and `rootfs.cpio.gz`.
2. The host launches QEMU through [collect_trace_run.sh](/home/ahmad/.ssh/Scheduler_sh/scripts/collect_trace_run.sh).
3. The guest boots via [init](/home/ahmad/.ssh/Scheduler_sh/rootfs/init) and runs the autorun trace collector.
4. Guest workloads execute and scheduler events are emitted as `[SCHED_TRACE]` lines.
5. Host-side collection stores `raw.log` and extracts `sched_trace.log`.
6. [analyze_trace.py](/home/ahmad/.ssh/Scheduler_sh/scripts/analyze_trace.py) normalizes the trace and computes metrics.
7. [benchmark_runner.py](/home/ahmad/.ssh/Scheduler_sh/scripts/benchmark_runner.py) repeats this flow across manifests and writes batch summaries.
8. [generate_plots.py](/home/ahmad/.ssh/Scheduler_sh/scripts/generate_plots.py) exports CSVs and PNG artifacts for interpretation.

## Key Components

- [linux/kernel/sched/core.c](/home/ahmad/.ssh/Scheduler_sh/linux/kernel/sched/core.c): enqueue, dequeue, and preempt tracing
- [linux/kernel/sched/fair.c](/home/ahmad/.ssh/Scheduler_sh/linux/kernel/sched/fair.c): next-task tracing and controlled scheduler modification
- [rootfs/init](/home/ahmad/.ssh/Scheduler_sh/rootfs/init): guest boot and autorun orchestration
- [scripts/collect_trace_run.sh](/home/ahmad/.ssh/Scheduler_sh/scripts/collect_trace_run.sh): host-side QEMU collection
- [analysis/parser.py](/home/ahmad/.ssh/Scheduler_sh/analysis/parser.py): structured event extraction
- [analysis/metrics.py](/home/ahmad/.ssh/Scheduler_sh/analysis/metrics.py): metric computation
- [scripts/benchmark_runner.py](/home/ahmad/.ssh/Scheduler_sh/scripts/benchmark_runner.py): repeatable multi-run experiments
- [scripts/generate_plots.py](/home/ahmad/.ssh/Scheduler_sh/scripts/generate_plots.py): visualization outputs

## Design Choices

- `trace_printk()` was used for bring-up speed and simple verification.
- The trace format uses short `key=value` pairs to simplify parsing.
- The benchmark runner reuses the same collection and analysis path instead of maintaining a separate experiment codepath.
- The scheduler modification is compile-time and local to `fair.c` so it can be reasoned about in isolation.
