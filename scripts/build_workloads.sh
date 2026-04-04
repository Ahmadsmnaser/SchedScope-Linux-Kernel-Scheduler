#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$ROOT_DIR/workloads/src"
BIN_DIR="$ROOT_DIR/workloads/bin"

mkdir -p "$BIN_DIR"

gcc -O2 -Wall -Wextra -static -o "$BIN_DIR/cpu_bound" "$SRC_DIR/cpu_bound.c"
gcc -O2 -Wall -Wextra -static -o "$BIN_DIR/sleep_burst" "$SRC_DIR/sleep_burst.c"

echo "Built workload binaries in $BIN_DIR"
