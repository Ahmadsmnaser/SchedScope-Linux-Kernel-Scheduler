.PHONY: help build-workloads build-initramfs build-kernel collect analyze benchmark-baseline benchmark-modified plots

help:
	@printf "SchedScope commands\n"
	@printf "  make build-workloads      Build host workload binaries\n"
	@printf "  make build-initramfs      Rebuild rootfs.cpio.gz from rootfs/\n"
	@printf "  make build-kernel         Rebuild linux/arch/x86/boot/bzImage\n"
	@printf "  make collect RUN=run_01   Collect one traced QEMU run\n"
	@printf "  make analyze RUN=run_01   Normalize and analyze one run\n"
	@printf "  make benchmark-baseline   Run baseline benchmark manifest\n"
	@printf "  make benchmark-modified   Run modified-scheduler benchmark manifest\n"
	@printf "  make plots RUN=run_01     Generate CSVs and PNG plots for one run\n"

build-workloads:
	bash scripts/build_workloads.sh

build-initramfs:
	bash scripts/build_initramfs.sh rootfs rootfs.cpio.gz

build-kernel:
	$(MAKE) -C linux -j"$$(nproc)" bzImage

collect:
	bash scripts/collect_trace_run.sh --run-name "$(or $(RUN),run_01)"

analyze:
	python3 scripts/analyze_trace.py results/$(or $(RUN),run_01)/sched_trace.log

benchmark-baseline:
	python3 scripts/benchmark_runner.py --manifest benchmarks/baseline_runs.json --summary results/summary.csv

benchmark-modified:
	python3 scripts/benchmark_runner.py --manifest benchmarks/phase8_modified_runs.json --summary results/phase8_modified_summary.csv

plots:
	python3 scripts/generate_plots.py results/$(or $(RUN),run_01)
