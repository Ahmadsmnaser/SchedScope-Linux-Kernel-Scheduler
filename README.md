# SchedScope

SchedScope is a Linux kernel scheduler experimentation project that runs a custom kernel inside QEMU, emits structured scheduler traces, executes controlled workloads, computes metrics, and compares baseline versus modified behavior.

The repository now covers:

- kernel bring-up and controlled boot in QEMU
- scheduler instrumentation with `[SCHED_TRACE]` events
- reproducible workload execution
- trace capture, normalization, and metrics export
- batch benchmark execution
- a small controlled scheduler modification
- CSV and plot generation for analysis

## Architecture

High-level flow:

1. Build the Linux kernel and initramfs.
2. Boot the kernel in QEMU with an autorun-enabled rootfs.
3. Run guest workloads and collect scheduler trace output.
4. Filter and normalize trace events on the host.
5. Compute metrics and batch summaries.
6. Generate CSVs and plots for inspection.

Supporting docs:

- [Architecture Overview](/home/ahmad/.ssh/Scheduler_sh/docs/architecture.md)
- [Experiments Guide](/home/ahmad/.ssh/Scheduler_sh/docs/experiments.md)
- [AI Workflow Notes](/home/ahmad/.ssh/Scheduler_sh/docs/ai_workflow.md)
- [Lessons Learned](/home/ahmad/.ssh/Scheduler_sh/docs/lessons_learned.md)
- [Original Phase Plan](/home/ahmad/.ssh/Scheduler_sh/markdown.md)

## Repository Layout

- [linux](/home/ahmad/.ssh/Scheduler_sh/linux): Linux kernel source and scheduler modifications
- [rootfs](/home/ahmad/.ssh/Scheduler_sh/rootfs): BusyBox-based guest filesystem
- [workloads](/home/ahmad/.ssh/Scheduler_sh/workloads): workload sources and configs
- [scripts](/home/ahmad/.ssh/Scheduler_sh/scripts): build, run, analysis, benchmark, and plotting tools
- [analysis](/home/ahmad/.ssh/Scheduler_sh/analysis): trace parsing and metric computation
- [benchmarks](/home/ahmad/.ssh/Scheduler_sh/benchmarks): benchmark manifests
- [results](/home/ahmad/.ssh/Scheduler_sh/results): collected run outputs
- [plots](/home/ahmad/.ssh/Scheduler_sh/plots): generated visual artifacts
- [docs](/home/ahmad/.ssh/Scheduler_sh/docs): project documentation

## Quick Start

Build workload binaries:

```bash
bash scripts/build_workloads.sh
```

Build the initramfs:

```bash
bash scripts/build_initramfs.sh rootfs rootfs.cpio.gz
```

Build the kernel:

```bash
make -C linux -j"$(nproc)" bzImage
```

Run one trace collection:

```bash
bash scripts/collect_trace_run.sh --run-name run_01
```

Analyze one collected trace:

```bash
python3 scripts/analyze_trace.py results/run_01/sched_trace.log
```

Run a benchmark batch:

```bash
python3 scripts/benchmark_runner.py --manifest benchmarks/baseline_runs.json
```

Generate CSVs and plots for a run:

```bash
python3 scripts/generate_plots.py results/phase8_vruntime_bias_01 --summary-csv results/phase8_modified_summary.csv
```

## Example Experiments

Baseline benchmark:

```bash
python3 scripts/benchmark_runner.py --manifest benchmarks/baseline_runs.json --summary results/summary.csv
```

Modified scheduler benchmark:

```bash
python3 scripts/benchmark_runner.py --manifest benchmarks/phase8_modified_runs.json --summary results/phase8_modified_summary.csv
```

Key outputs per run:

- `raw.log`
- `sched_trace.log`
- `normalized_events.jsonl`
- `normalized_events.csv`
- `metrics_summary.json`
- `metrics_summary.txt`
- `timeline_data.csv`
- `per_task_metrics.csv`

Key plot outputs:

- `plots/<run_name>/timeline.png`
- `plots/<run_name>/latency.png`
- `plots/<run_name>/fairness.png`

## Scheduler Modification

The controlled Phase 8 modification lives in [linux/kernel/sched/fair.c](/home/ahmad/.ssh/Scheduler_sh/linux/kernel/sched/fair.c).

It adds a small compile-time vruntime placement bias:

- `SCHEDSCOPE_VRUNTIME_PLACEMENT_BIAS`
- `SCHEDSCOPE_VRUNTIME_BIAS_STEP_NS`

The change is intentionally small and isolated so baseline and modified runs stay easy to compare.

## Phase Status

- Phase 1: complete
- Phase 2: complete
- Phase 3: complete
- Phase 4: complete
- Phase 5: complete for capture/filter; normalization was completed as part of Phase 6
- Phase 6: complete
- Phase 7: complete
- Phase 8: complete
- Phase 9: complete
- Phase 10: complete

## Validation Notes

Validated in this workspace:

- kernel rebuild with scheduler instrumentation
- guest boot and autorun flow in QEMU
- trace collection into per-run result directories
- normalization and metrics export
- benchmark batch execution
- modified scheduler boot and benchmark execution
- CSV and PNG artifact generation

Current caveats:

- some per-task naming is inferred from trace context and can remain coarse for long-lived shell-driven task chains
- turnaround and throughput include inferred values because the trace schema does not emit an explicit completion event

## AI Brief

The separate mini-scheduler brief remains available at:

- [MINI_SCHEDULER_AI_BRIEF.md](/home/ahmad/.ssh/Scheduler_sh/MINI_SCHEDULER_AI_BRIEF.md)
