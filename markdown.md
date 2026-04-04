# SchedScope — Linux Kernel Scheduler Experimentation Project

## Overview
SchedScope is a Linux kernel-based scheduler experimentation framework running inside QEMU.  
The project focuses on observing, analyzing, and modifying scheduling behavior (primarily CFS-like) and comparing it against baseline policies (e.g., Round Robin) using controlled workloads and measurable metrics.

The system is composed of:
- Kernel-level instrumentation and optional scheduling modifications
- Config-driven workload generation
- Automated experiment execution
- Trace collection and parsing
- Metrics computation and analysis

---

# Phase 1 — Environment Setup & Kernel Control

## Goal
Establish a fully controlled Linux kernel development and execution environment inside QEMU.

## Steps

1. **Clone Linux Kernel Source**
   - Use a stable version (e.g., v6.x LTS)
   - Maintain a clean branch for experimentation

2. **Setup Build Environment**
   - Install required dependencies:
     - gcc, make, flex, bison, libssl-dev, libelf-dev, qemu, etc.

3. **Kernel Configuration**
   - Use `defconfig` as baseline
   - Enable:
     - CONFIG_SCHED_DEBUG
     - CONFIG_FTRACE (optional but recommended)
     - CONFIG_DEBUG_KERNEL

4. **Build Kernel**
   - Compile kernel image (`bzImage`)
   - Ensure no build errors

5. **Prepare Root Filesystem**
   - Minimal rootfs (BusyBox recommended)
   - Include:
     - shell
     - basic utilities
     - ability to run custom workloads

6. **Run Kernel in QEMU**
   - Boot kernel with rootfs
   - Validate:
     - successful boot
     - shell access

7. **Validation Step**
   - Modify a trivial kernel log (`printk`)
   - Rebuild and verify change appears in QEMU output

---

# Phase 2 — Scheduler Code Exploration

## Goal
Understand and isolate key scheduling code paths for instrumentation.

## Steps

1. **Identify Key Files**
   - `kernel/sched/core.c`
   - `kernel/sched/fair.c`
   - `kernel/sched/rt.c`

2. **Trace Core Scheduling Flow**
   - Focus on:
     - `schedule()`
     - `pick_next_task_*`
     - `enqueue_task_*`
     - `dequeue_task_*`
     - `task_tick_*`

3. **Understand Data Structures**
   - `task_struct`
   - `sched_entity`
   - runqueue (`rq`)
   - CFS tree (red-black tree)

4. **Document Findings**
   - Write short internal notes:
     - how a task enters runqueue
     - how next task is selected
     - what triggers preemption

---

# Phase 3 — Kernel Instrumentation Layer

## Goal
Introduce controlled tracing of scheduling decisions.

## Steps

1. **Define Trace Schema**
   Each log entry should include:
   - timestamp
   - CPU id
   - current task (pid)
   - next task (pid)
   - task priority / nice
   - scheduling reason (if possible)
   - runtime / vruntime (if accessible)

2. **Add Instrumentation Points**
   Suggested locations:
   - before/after `pick_next_task`
   - inside `enqueue_task`
   - inside `dequeue_task`
   - during `task_tick`

3. **Logging Mechanism**
   - Use `printk` initially
   - Optional:
     - debugfs interface
     - custom tracepoints (advanced)

4. **Standardize Output Format**
   Example:
    [SCHED_TRACE] ts=... cpu=... prev=... next=... vruntime=... nice=...


5. **Rebuild & Validate**
- Run kernel
- Confirm logs are:
  - consistent
  - parseable
  - not excessively noisy

---

# Phase 4 — Workload Generation Framework

## Goal
Create controlled and reproducible workloads.

## Steps

1. **Define Workload Types**
- CPU-bound tasks
- IO/sleep-heavy tasks
- mixed workloads
- priority-skewed workloads

2. **Implement Workload Programs**
- Small C programs:
  - busy loop (CPU-bound)
  - sleep + burst cycles (IO-like)
  - configurable behavior

3. **Config-Driven Execution**
- Use JSON/YAML config:
  ```json
  {
    "tasks": [
      {"type": "cpu", "duration": 5000, "nice": 0, "start_delay": 0},
      {"type": "io", "pattern": [100, 200], "nice": 5, "start_delay": 100}
    ]
  }
  ```

4. **Workload Launcher**
- Python script:
  - reads config
  - spawns tasks accordingly
  - controls timing and parameters

5. **Validation**
- Ensure workloads behave deterministically
- Confirm variation across different configs

---

# Phase 5 — Trace Collection Pipeline

## Goal
Extract and persist scheduler traces for analysis.

## Steps

1. **Capture Kernel Output**
- Redirect QEMU output to file
- Alternatively use `dmesg`

2. **Filter Relevant Logs**
- Extract only `[SCHED_TRACE]` entries

3. **Store Raw Logs**
- Organized per run:
  ```
  results/run_01/raw.log
  ```

4. **Normalize Data**
- Convert logs to structured format:
  - CSV or JSON

---

# Phase 6 — Metrics & Analysis Engine

## Goal
Compute meaningful scheduling metrics from traces.

## Steps

1. **Implement Parser**
- Parse logs into structured events:
  - task switches
  - execution intervals

2. **Compute Metrics**
- waiting time
- turnaround time
- response time
- throughput
- CPU utilization
- context switches
- fairness indicator
- starvation detection

3. **Per-Task Statistics**
- runtime
- number of preemptions
- wakeups

4. **Aggregate Metrics**
- averages
- distributions
- percentiles

5. **Export Results**
- CSV files
- structured summaries

---

# Phase 7 — Benchmark Framework

## Goal
Enable repeatable experiments across configurations.

## Steps

1. **Experiment Runner**
- Automate:
  - kernel boot
  - workload execution
  - trace collection
  - metric computation

2. **Multiple Runs Support**
- Allow batch execution with different configs

3. **Baseline Comparison**
- Compare:
  - default CFS behavior
  - RR (or equivalent baseline)

4. **Result Organization**
results/
├── run_01/
├── run_02/
└── summary.csv


---

# Phase 8 — Scheduler Modification (Controlled)

## Goal
Introduce a minimal, controlled change to scheduling behavior.

## Steps

1. **Select Modification Area**
Examples:
- time slice adjustment
- vruntime weighting tweak
- priority bias

2. **Implement Change**
- Keep modification:
  - isolated
  - toggleable (compile flag or macro)

3. **Ensure Stability**
- no crashes
- no infinite loops
- no starvation bugs (unless intentional for experiment)

4. **Run Experiments**
- baseline vs modified behavior

5. **Analyze Impact**
- compare metrics
- identify trade-offs

---

# Phase 9 — Visualization Layer

## Goal
Provide simple, clear representation of scheduling behavior.

## Steps

1. **Generate CSV Outputs**
- timeline data
- per-task metrics

2. **Plot Graphs**
- using Python (matplotlib):
  - Gantt-like timeline
  - latency distribution
  - fairness comparison

3. **Save Artifacts**
plots/
├── timeline.png
├── latency.png
└── fairness.png


---

# Phase 10 — Documentation & Presentation

## Goal
Make the project understandable, reproducible, and interview-ready.

## Steps

1. **Write README**
Include:
- project purpose
- architecture overview
- how to run
- example experiments

2. **Architecture Document**
- system design
- data flow
- key components

3. **Experiments Document**
- workload definitions
- experiment setup
- results and observations

4. **AI-Assisted Workflow Documentation**
- where AI was used
- what was validated manually
- mistakes and corrections

5. **Lessons Learned**
- kernel challenges
- debugging insights
- scheduling trade-offs

---

# Phase 11 — Repository Structure
schedscope/
├── kernel_patches/
├── workloads/
├── scripts/
├── results/
├── plots/
├── docs/
├── README.md
└── Makefile

---

# Final Outcome

The system should:
- run a custom Linux kernel inside QEMU
- trace scheduling decisions in real time
- execute configurable workloads
- compute and compare scheduling metrics
- demonstrate controlled scheduler modifications
- provide reproducible experiments
- be fully documented and explainable
