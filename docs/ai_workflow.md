# AI-Assisted Workflow

## Where AI Was Used

AI assistance was used to:

- inspect the repository and compare implementation against the original phase plan
- implement host-side analysis, benchmarking, and visualization tooling
- add a small controlled scheduler modification
- write and organize project documentation

## What Was Validated Manually

Manual or execution-based validation included:

- checking that kernel instrumentation was present in the expected scheduler files
- rebuilding the Linux kernel after scheduler changes
- booting the kernel in QEMU
- collecting real trace logs into the `results/` directory
- running the analysis pipeline on captured traces
- running the benchmark runner on baseline and modified kernels
- generating CSV and PNG artifacts from a real run directory

## Mistakes And Corrections

Notable corrections during the workflow:

- Phase 5 was initially marked complete in the repository notes, but the original plan still required normalized CSV/JSON export. That gap was closed during Phase 6.
- The first version of `analyze_trace.py` failed because the repository root was not on `sys.path`. The script was updated to import local analysis modules correctly.
- The first metrics attribution pass attached task names too loosely from trace lines. The logic was tightened so task identity tracking is less misleading.
- The first plotting attempt assumed `matplotlib` was installed. The visualization step was rewritten to generate PNG files without external plotting dependencies.

## Working Principles That Helped

- keep each phase incremental and testable
- prefer small isolated changes over broad refactors
- validate through real run artifacts whenever possible
- keep benchmark, analysis, and plotting flows separate so failures are easier to localize
