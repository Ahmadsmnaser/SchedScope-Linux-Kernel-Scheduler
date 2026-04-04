# Mini Scheduler Build Instructions

This file is a build brief for an AI model.

Your job is not to extend the full Linux kernel scheduler project.
Your job is to build a much smaller scheduler simulation that captures the core ideas:

- tasks become runnable
- tasks enter a runqueue
- a scheduler selects the next task
- preemption can occur
- traces are emitted
- metrics can be computed from those traces

The target is a mini scheduler, not a real kernel scheduler.

## Mission

Build a small, deterministic scheduler framework that is easy to explain, easy to test, and easy to instrument.

The final system should:

- simulate scheduling decisions in user space
- support at least one fair-style policy
- optionally support a simple baseline like Round Robin
- emit structured scheduler traces
- run configurable workloads
- compute basic metrics
- stay small enough to understand end to end

## Hard Rules

- Do not build new kernel features unless explicitly requested.
- Do not depend on QEMU or kernel rebuilds for the mini scheduler itself.
- Keep the implementation in user space.
- Prefer clarity over realism.
- Prefer deterministic behavior over complex concurrency.
- Every scheduling decision must be traceable.
- Every trace line must be parseable.
- Keep the project small enough that one person can explain every file.

## Lessons Learned From The Larger Project

- Full kernel experimentation works, but it is heavy and slow for iteration.
- Incremental kernel rebuilds are much faster than full rebuilds, but still expensive compared to a user-space simulator.
- `trace_printk()` works, but long trace messages become messy on the serial console.
- Short trace lines are better than verbose trace lines.
- Repeating the function name inside the trace payload is unnecessary when ftrace already shows it.
- A good trace format is more valuable than a clever trace format.
- The most important scheduler concepts are:
  - task activation
  - enqueue
  - dequeue
  - next-task selection
  - preemption
- The important mental model from Linux scheduling is:
  - wakeup path -> activate task -> enqueue task
  - schedule path -> pick next task
  - preemption decision -> mark reschedule -> switch later

## Conceptual Model To Implement

The mini scheduler should model these objects:

- `Task`
  - `id`
  - `name`
  - `state`
  - `nice` or priority
  - `remaining_runtime`
  - `vruntime` for fair scheduling
  - `arrival_time`
  - `first_run_time`
  - `finish_time`

- `RunQueue`
  - list or heap of runnable tasks
  - current task
  - current time
  - number of runnable tasks

- `Scheduler`
  - enqueue task
  - dequeue task
  - pick next task
  - tick
  - maybe preempt current task

- `TraceEvent`
  - timestamp
  - cpu
  - prev task id
  - next task id
  - task nice
  - vruntime if applicable
  - reason

## Scheduler Policies

Implement these in order:

1. Round Robin
- easiest baseline
- fixed time slice
- simple validation policy

2. Mini Fair Scheduler
- choose the runnable task with the smallest `vruntime`
- update `vruntime` while a task runs
- weight runtime by `nice` if you want a simple fairness model

Do not implement the full Linux EEVDF design unless explicitly requested.
A simplified fair scheduler is enough.

## Required Trace Format

Use one short structured line per event.

Preferred format:

```text
[SCHED_TRACE] ts=120 cpu=0 prev=2 next=5 vruntime=340 nice=0 reason=pick_next
```

Rules:

- every line starts with `[SCHED_TRACE]`
- use key=value pairs
- keep the line short
- keep field names stable
- do not print human-only filler text

Required event types:

- `enqueue`
- `dequeue`
- `pick_next`
- `tick`
- `preempt`
- `complete`

## Workload Rules

Support a small config-driven workload format.

Example:

```json
{
  "policy": "fair",
  "tick_ns": 1000000,
  "tasks": [
    { "id": 1, "name": "A", "arrival": 0, "runtime": 12, "nice": 0 },
    { "id": 2, "name": "B", "arrival": 3, "runtime": 8, "nice": 5 },
    { "id": 3, "name": "C", "arrival": 5, "runtime": 20, "nice": -3 }
  ]
}
```

The simulator should:

- load the config
- inject tasks at their arrival times
- run ticks until all tasks finish
- emit traces
- write metrics

## Metrics To Compute

Compute at least:

- waiting time
- turnaround time
- response time
- completion time
- number of context switches
- per-task runtime
- fairness summary

Optional:

- starvation detection
- throughput
- utilization

## Implementation Rules For The AI Model

- Build the smallest working version first.
- Start with a single CPU only.
- Start with deterministic ticks, not wall-clock time.
- Avoid threads unless explicitly needed.
- Prefer pure functions for policy logic where possible.
- Keep policy logic separate from trace writing.
- Keep trace writing separate from metrics parsing.
- Make output reproducible from the same input config.

## Suggested Project Structure

```text
mini_scheduler/
├── README.md
├── configs/
├── scheduler/
│   ├── models.py
│   ├── queue.py
│   ├── policies.py
│   ├── engine.py
│   └── tracing.py
├── analysis/
│   ├── parser.py
│   └── metrics.py
├── scripts/
│   └── run_simulation.py
├── results/
└── tests/
```

If another language is chosen, preserve the same separation of concerns.

## Build Plan

Phase A - Minimal Engine
- define task and runqueue models
- implement tick loop
- implement enqueue and completion

Phase B - Round Robin
- fixed quantum
- context-switch tracing
- validate with 2 to 3 simple tasks

Phase C - Mini Fair Scheduler
- add `vruntime`
- pick smallest `vruntime`
- update `vruntime` every tick
- trace pick and preempt decisions

Phase D - Config Loader
- load workload JSON
- support arrival times and nice values

Phase E - Metrics
- parse traces
- compute per-task metrics
- export results

Phase F - Comparison
- run the same workload under RR and Fair
- compare waiting time, turnaround time, and fairness

## Validation Rules

The AI model must verify:

- a single task runs to completion
- multiple equal tasks are scheduled fairly
- Round Robin rotates tasks by quantum
- a newly arrived task is enqueued correctly
- preemption logic works under the chosen policy
- trace lines are parseable with no special-case hacks

## What Not To Do

- do not copy Linux kernel code into the mini scheduler
- do not implement kernel locking complexity
- do not implement multi-core support in version 1
- do not implement cgroups in version 1
- do not build an overly abstract framework before the simulator works
- do not hide policy decisions inside unrelated utility code

## Useful Reference Concepts From Linux

These ideas are worth preserving conceptually:

- task activation is distinct from task selection
- preemption decision is distinct from actual switch
- runqueue state is the source of truth
- fair scheduling can be approximated through `vruntime`
- short structured traces are critical for debugging

These Linux-specific details are not required in version 1:

- full EEVDF behavior
- kernel tracepoints
- `rq_flags`
- cgroup hierarchy scheduling
- SMP balancing
- kernel-specific locking

## Output Expected From The AI Model

The AI model should produce:

- a working mini scheduler
- a small set of workload configs
- structured trace logs
- a parser for those logs
- metrics output
- a short explanation of how enqueue, pick-next, and preemption work

## Current Repo Context

This repository also contains a larger Linux/QEMU scheduler experiment environment.
That work proved useful ideas, but it is no longer the primary target.

If using this repo as a base, treat the kernel/QEMU work as reference material only.
The new primary goal is the mini scheduler described in this file.
