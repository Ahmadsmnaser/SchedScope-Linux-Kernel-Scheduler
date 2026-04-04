#!/bin/sh

WORKLOAD_DIR="/workloads/bin"

echo "[WORKLOAD] starting mixed workload"

"$WORKLOAD_DIR/cpu_bound" 5000 &
CPU_A_PID=$!

sleep 0.05
"$WORKLOAD_DIR/sleep_burst" 100 200 20 &
IO_PID=$!

sleep 0.05
"$WORKLOAD_DIR/cpu_bound" 5000 &
CPU_B_PID=$!
/renice 5 "$CPU_B_PID" >/dev/null

echo "[WORKLOAD] pids: cpu_a=$CPU_A_PID io_like_a=$IO_PID cpu_b=$CPU_B_PID"

wait "$CPU_A_PID"
wait "$IO_PID"
wait "$CPU_B_PID"

echo "[WORKLOAD] mixed workload complete"
