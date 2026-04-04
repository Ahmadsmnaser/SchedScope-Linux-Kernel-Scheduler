# Lessons Learned

## Kernel Challenges

- full kernel experimentation is slower than user-space work, so small isolated modifications matter a lot
- `trace_printk()` is useful for bring-up, but trace volume grows quickly once workloads become active
- guest automation helps, but serial/QEMU lifecycle details still shape how convenient the workflow feels

## Debugging Insights

- short structured trace lines are much easier to parse and validate than verbose ad hoc logs
- separating guest-side collection from host-side filtering keeps failure boundaries clearer
- benchmark automation becomes reliable faster when it reuses the same single-run pipeline instead of inventing a second path

## Scheduling Trade-Offs

- even a very small placement bias can visibly change context-switch and preemption behavior
- fairness interpretation depends heavily on how tasks are identified and how completion is inferred
- benchmark comparisons should be repeated before drawing strong conclusions from one run

## Project Takeaways

- the repository is now reproducible enough for guided demos and technical discussion
- the strongest next improvement would be tighter workload identity tracking and repeated A/B experiment batches
- the combination of trace capture, metrics, and visuals gives a much better story than any one layer alone
