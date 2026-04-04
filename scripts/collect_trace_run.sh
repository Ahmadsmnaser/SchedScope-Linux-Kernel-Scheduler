#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS_DIR="$ROOT_DIR/results"
RUN_NAME="run_$(date +%Y%m%d_%H%M%S)"
TIMEOUT_SECONDS=60
KERNEL_APPEND_EXTRA=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name)
      RUN_NAME="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT_SECONDS="$2"
      shift 2
      ;;
    --kernel-append)
      KERNEL_APPEND_EXTRA="$2"
      shift 2
      ;;
    *)
      RUN_NAME="$1"
      shift
      ;;
  esac
done

RUN_DIR="$RESULTS_DIR/$RUN_NAME"
RAW_LOG="$RUN_DIR/raw.log"
FILTERED_LOG="$RUN_DIR/sched_trace.log"
KERNEL_APPEND="console=ttyS0 rdinit=/init nokaslr schedscope_autorun=1"

if [[ -n "$KERNEL_APPEND_EXTRA" ]]; then
  KERNEL_APPEND="$KERNEL_APPEND $KERNEL_APPEND_EXTRA"
fi

mkdir -p "$RUN_DIR"

set +e
timeout "${TIMEOUT_SECONDS}s" qemu-system-x86_64 \
  -kernel "$ROOT_DIR/linux/arch/x86/boot/bzImage" \
  -initrd "$ROOT_DIR/rootfs.cpio.gz" \
  -append "$KERNEL_APPEND" \
  -m 1024 \
  -smp 1 \
  -nographic \
  -no-reboot \
  >"$RAW_LOG" 2>&1
QEMU_STATUS=$?
set -e

if [[ "$QEMU_STATUS" -ne 0 && "$QEMU_STATUS" -ne 124 ]]; then
  echo "QEMU collection run failed with status $QEMU_STATUS" >&2
  exit "$QEMU_STATUS"
fi

grep '\[SCHED_TRACE\]' "$RAW_LOG" > "$FILTERED_LOG" || true

printf 'Created %s\n' "$RUN_DIR"
printf 'Raw log: %s\n' "$RAW_LOG"
printf 'Filtered trace: %s\n' "$FILTERED_LOG"
